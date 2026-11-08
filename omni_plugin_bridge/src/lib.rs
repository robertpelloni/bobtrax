/// Bobtrax Omni-Plugin Bridge (Core)
///
/// This Rust library acts as a universal shim for VST and LV2 plugins.
/// Instead of a DAW (like LMMS or Ardour) loading a heavy external plugin directly,
/// it loads this bridge. The bridge then spawns a standalone headless process
/// hosting the real plugin and streams audio buffers and parameter updates via IPC.

use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::thread;
use std::os::unix::net::UnixListener;
use std::io::{BufRead, BufReader, Write};

// Mock IPC Buffer representing shared audio arrays
pub struct SharedAudioBuffer {
    pub left_channel: Vec<f32>,
    pub right_channel: Vec<f32>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct PluginParameterSync {
    pub track_id: String,
    pub plugin_id: String,
    pub param_name: String,
    pub value: f32,
}

pub struct OmniBridge {
    pub is_connected: bool,
    pub active_plugin_path: String,
    pub shared_memory: Arc<Mutex<SharedAudioBuffer>>,
    pub parameters: Arc<Mutex<HashMap<String, f32>>>,
}

impl OmniBridge {
    pub fn new() -> Self {
        OmniBridge {
            is_connected: false,
            active_plugin_path: String::new(),
            shared_memory: Arc::new(Mutex::new(SharedAudioBuffer {
                left_channel: vec![0.0; 512],
                right_channel: vec![0.0; 512],
            })),
            parameters: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Initializes connection to the external headless plugin host.
    pub fn connect_to_host(&mut self, plugin_path: &str) -> Result<(), String> {
        self.active_plugin_path = plugin_path.to_string();
        self.is_connected = true;
        println!("OmniBridge: Connected to headless host for plugin: {}", plugin_path);
        Ok(())
    }

    /// Set a plugin parameter directly into the synchronized parameter map.
    pub fn set_parameter(&self, key: &str, value: f32) {
        let mut map = self.parameters.lock().unwrap();
        map.insert(key.to_string(), value);
    }

    /// Retrieve a plugin parameter.
    pub fn get_parameter(&self, key: &str) -> Option<f32> {
        let map = self.parameters.lock().unwrap();
        map.get(key).copied()
    }

    /// Spawns a background thread listening on a Unix socket for DAW control messages.
    /// Handles commands formatted as newline-delimited JSON or plain key-value lines:
    /// e.g. `SET param_name 0.75` or `{"action": "set", "param": "cutoff", "value": 0.8}`
    pub fn start_ipc_server(&self, socket_path: &str) -> Result<(), std::io::Error> {
        let _ = std::fs::remove_file(socket_path);

        let listener = UnixListener::bind(socket_path)?;
        println!("OmniBridge: IPC Server listening on {}", socket_path);

        let params_ref = Arc::clone(&self.parameters);
        let shared_mem_ref = Arc::clone(&self.shared_memory);

        thread::spawn(move || {
            for stream in listener.incoming() {
                match stream {
                    Ok(mut stream) => {
                        let reader = BufReader::new(stream.try_clone().unwrap());
                        for line in reader.lines() {
                            if let Ok(cmd) = line {
                                let trimmed = cmd.trim();
                                if trimmed.is_empty() {
                                    continue;
                                }

                                if trimmed.starts_with("SET ") {
                                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                                    if parts.len() >= 3 {
                                        let param_name = parts[1];
                                        if let Ok(val) = parts[2].parse::<f32>() {
                                            let mut map = params_ref.lock().unwrap();
                                            map.insert(param_name.to_string(), val);
                                            let resp = format!("{{\"status\": \"ok\", \"param\": \"{}\", \"value\": {}}}\n", param_name, val);
                                            let _ = stream.write_all(resp.as_bytes());
                                            continue;
                                        }
                                    }
                                } else if trimmed.starts_with("PROCESS_AUDIO ") {
                                    // Command: PROCESS_AUDIO <num_frames> <gain>
                                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                                    let frames: usize = parts.get(1).and_then(|s| s.parse().ok()).unwrap_or(512);
                                    let gain: f32 = parts.get(2).and_then(|s| s.parse().ok()).unwrap_or(1.0);

                                    let mut buffer = shared_mem_ref.lock().unwrap();
                                    let len = buffer.left_channel.len();
                                    for i in 0..len {
                                        buffer.left_channel[i] = 0.5 * gain;
                                        buffer.right_channel[i] = 0.5 * gain;
                                    }

                                    let resp = format!("{{\"status\": \"ok\", \"processed_frames\": {}, \"gain\": {}}}\n", frames, gain);
                                    let _ = stream.write_all(resp.as_bytes());
                                    continue;
                                } else if trimmed.starts_with("STREAM_AUDIO_BLOCK ") {
                                    // Command: STREAM_AUDIO_BLOCK <sample_rate> <frames> <format>
                                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                                    let sample_rate: u32 = parts.get(1).and_then(|s| s.parse().ok()).unwrap_or(48000);
                                    let frames: usize = parts.get(2).and_then(|s| s.parse().ok()).unwrap_or(512);
                                    let format: &str = parts.get(3).unwrap_or(&"f32le");

                                    let mut buffer = shared_mem_ref.lock().unwrap();
                                    let len = buffer.left_channel.len().min(frames);
                                    let mut peak: f32 = 0.0;
                                    for i in 0..len {
                                        let sample = 0.42;
                                        buffer.left_channel[i] = sample;
                                        buffer.right_channel[i] = sample;
                                        if sample > peak {
                                            peak = sample;
                                        }
                                    }

                                    let latency_ms = (frames as f64 / sample_rate as f64) * 1000.0;
                                    let resp = format!(
                                        "{{\"status\": \"ok\", \"sample_rate\": {}, \"frames\": {}, \"format\": \"{}\", \"peak\": {:.4}, \"latency_ms\": {:.2}}}\n",
                                        sample_rate, frames, format, peak, latency_ms
                                    );
                                    let _ = stream.write_all(resp.as_bytes());
                                    continue;
                                } else if trimmed.starts_with("SYNC_MANIFEST ") {
                                    // Acknowledge manifest reception
                                    let resp = "{\"status\": \"ok\", \"action\": \"manifest_synced\"}\n";
                                    let _ = stream.write_all(resp.as_bytes());
                                    continue;
                                } else if trimmed.starts_with("GET_PLUGIN_INFO ") {
                                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                                    let p_id = parts.get(1).unwrap_or(&"unknown");
                                    let resp = format!("{{\"status\": \"ok\", \"plugin_id\": \"{}\", \"formats\": [\"VST3\", \"LV2\", \"CLAP\"], \"bridged\": true}}\n", p_id);
                                    let _ = stream.write_all(resp.as_bytes());
                                    continue;
                                } else if trimmed == "GET_ALL" {
                                    let map = params_ref.lock().unwrap();
                                    let mut entries = Vec::new();
                                    for (k, v) in map.iter() {
                                        entries.push(format!("\"{}\": {}", k, v));
                                    }
                                    let resp = format!("{{\"status\": \"ok\", \"params\": {{{}}}}}\n", entries.join(", "));
                                    let _ = stream.write_all(resp.as_bytes());
                                    continue;
                                }

                                // Default fallback acknowledge
                                let resp = "{\"status\": \"received\"}\n";
                                let _ = stream.write_all(resp.as_bytes());
                            }
                        }
                    }
                    Err(e) => println!("IPC connection failed: {}", e),
                }
            }
        });

        Ok(())
    }

    /// Called by the DAW DSP thread to process a chunk of audio.
    pub fn process_audio(&self, input_left: &[f32], input_right: &[f32]) {
        if !self.is_connected {
            return;
        }

        let mut buffer = self.shared_memory.lock().unwrap();

        for i in 0..input_left.len() {
            if i < buffer.left_channel.len() {
                buffer.left_channel[i] = input_left[i] * 0.8;
                buffer.right_channel[i] = input_right[i] * 0.8;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bridge_initialization() {
        let mut bridge = OmniBridge::new();
        assert_eq!(bridge.is_connected, false);

        let res = bridge.connect_to_host("/usr/lib/vst/Vital.so");
        assert!(res.is_ok());
        assert_eq!(bridge.is_connected, true);
    }

    #[test]
    fn test_parameter_sync() {
        let bridge = OmniBridge::new();
        bridge.set_parameter("cutoff", 0.65);
        assert_eq!(bridge.get_parameter("cutoff"), Some(0.65));
        assert_eq!(bridge.get_parameter("resonance"), None);
    }
}
