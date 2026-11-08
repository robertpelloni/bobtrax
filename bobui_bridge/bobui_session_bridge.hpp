#ifndef BOBUI_SESSION_BRIDGE_HPP
#define BOBUI_SESSION_BRIDGE_HPP

#include <string>
#include <vector>
#include <map>
#include <cstdint>
#include <cstring>
#include <algorithm>

struct BobUITrackDescriptor {
    std::string name;
    std::string role;
    float fader;
    bool muted;
    bool soloed;
};

/**
 * BobUISessionBridge
 *
 * Native C++ bridge for exporting and importing session arrangements
 * across Ardour, LMMS, and BobUI.
 */
class BobUISessionBridge {
public:
    BobUISessionBridge() = default;
    ~BobUISessionBridge() = default;

    bool exportSessionToArdour(const std::vector<BobUITrackDescriptor>& tracks, const std::string& out_path);
    bool exportSessionToLMMS(const std::vector<BobUITrackDescriptor>& tracks, const std::string& out_path);
    std::vector<BobUITrackDescriptor> importSessionFromArdour(const std::string& in_path);

    bool saveCheckpoint(const std::string& name, const std::vector<BobUITrackDescriptor>& tracks);
    std::vector<BobUITrackDescriptor> restoreCheckpoint(const std::string& name);
    std::vector<BobUITrackDescriptor> undoLastAction();
    std::vector<BobUITrackDescriptor> redoSessionAction();

    // Low-Latency Binary Serialization for High-Speed Inter-DAW State Sync
    static std::vector<uint8_t> serializeTrackStateBinary(const BobUITrackDescriptor& track);
    static BobUITrackDescriptor deserializeTrackStateBinary(const std::vector<uint8_t>& bytes);

private:
    std::map<std::string, std::vector<BobUITrackDescriptor>> m_checkpoints;
    std::vector<std::vector<BobUITrackDescriptor>> m_undoHistory;
    std::vector<std::vector<BobUITrackDescriptor>> m_redoHistory;
};

#endif // BOBUI_SESSION_BRIDGE_HPP
