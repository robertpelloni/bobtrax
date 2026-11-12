//! Standalone Headless Plugin Host Server for Bobtrax Omni-Plugin Bridge
//!
//! Spawns an IPC Unix Domain Socket server and processes simulated
//! audio blocks across multiple connected DAWs (LMMS, Ardour).

use omni_bridge::OmniBridge;
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let socket_path = args.get(1).map(|s| s.as_str()).unwrap_or("/tmp/bobtrax_omni_bridge.sock");
    let plugin_path = args.get(2).map(|s| s.as_str()).unwrap_or("VirtualAnalogCompressor.so");

    println!("====================================================");
    println!("  Bobtrax Omni-Plugin Bridge Standalone Host");
    println!("====================================================");
    println!("• Socket Path : {}", socket_path);
    println!("• Plugin Target: {}", plugin_path);

    let mut bridge = OmniBridge::new();
    if let Err(e) = bridge.connect_to_host(plugin_path) {
        eprintln!("Failed to connect to host: {}", e);
        std::process::exit(1);
    }

    if let Err(e) = bridge.start_ipc_server(socket_path) {
        eprintln!("Failed to start IPC server: {}", e);
        std::process::exit(1);
    }

    // Process a test audio chunk
    let input_l = vec![0.5; 512];
    let input_r = vec![0.5; 512];
    bridge.process_audio(&input_l, &input_r);
    println!("• DSP Test    : 512 audio frames processed successfully.");
    println!("• Status      : IPC Host is live and listening on {}", socket_path);

    // Keep process alive while serving IPC requests
    loop {
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
}
