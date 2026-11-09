#ifndef BOBUI_OMNI_ADAPTER_HPP
#define BOBUI_OMNI_ADAPTER_HPP

#include <string>
#include <map>
#include <vector>
#include "bobui_session_bridge.hpp"

/**
 * BobUIOmniAdapter
 *
 * Provides native C++ cross-DAW parameter synchronization between
 * BobUI GUI components and the Rust Omni-Plugin Host over Unix Domain Sockets.
 */
class BobUIOmniAdapter {
public:
    explicit BobUIOmniAdapter(const std::string& socket_path = "/tmp/bobtrax_omni_bridge.sock");
    ~BobUIOmniAdapter();

    bool connect();
    void disconnect();
    bool isConnected() const;

    bool setParameter(const std::string& track_id, const std::string& plugin_id,
                      const std::string& param_name, float value);
    bool bulkSyncTracksBinary(const std::vector<BobUITrackDescriptor>& tracks);
    bool testAudioLoopback(size_t frames, float* peakOut = nullptr, float* rmsOut = nullptr);
    std::map<std::string, float> getAllParameters();

private:
    std::string m_socketPath;
    int m_socketFd;
};

#endif // BOBUI_OMNI_ADAPTER_HPP
