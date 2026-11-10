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
    float pan;
    bool muted;
    bool soloed;
    bool frozen;
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
    std::vector<BobUITrackDescriptor> importSessionFromLMMS(const std::string& in_path);

    bool saveCheckpoint(const std::string& name, const std::vector<BobUITrackDescriptor>& tracks);
    std::vector<BobUITrackDescriptor> restoreCheckpoint(const std::string& name);
    bool deleteCheckpoint(const std::string& name);
    size_t pruneCheckpoints(size_t maxCheckpoints);
    bool forkCheckpoint(const std::string& srcId, const std::string& newName, const std::string& branchTag = "");
    bool mergeCheckpointBranch(const std::string& srcId, const std::string& targetId);
    std::string getCheckpointParent(const std::string& id) const;
    bool validateTransitionPreflight(const std::string& fromDaw, const std::string& toDaw) const;
    std::map<std::string, std::string> simulateTransition(const std::string& fromDaw, const std::string& toDaw) const;
    bool stashSession(const std::vector<BobUITrackDescriptor>& tracks);
    std::vector<BobUITrackDescriptor> popStash();
    bool pingEngine(const std::string& dawName, double* latencyMs = nullptr) const;
    bool exportCheckpointsBundle(const std::string& outPath) const;
    bool importCheckpointsBundle(const std::string& inPath);
    std::map<std::string, std::string> getSessionMetrics() const;
    std::vector<std::string> listCheckpoints() const;
    std::vector<BobUITrackDescriptor> undoLastAction();
    std::vector<BobUITrackDescriptor> redoSessionAction();

    // Low-Latency Binary Serialization for High-Speed Inter-DAW State Sync
    static std::vector<uint8_t> serializeTrackStateBinary(const BobUITrackDescriptor& track);
    static BobUITrackDescriptor deserializeTrackStateBinary(const std::vector<uint8_t>& bytes);

private:
    std::map<std::string, std::vector<BobUITrackDescriptor>> m_checkpoints;
    std::map<std::string, std::string> m_checkpointParents;
    std::map<std::string, std::string> m_checkpointTags;
    std::vector<std::vector<BobUITrackDescriptor>> m_stashStack;
    std::vector<std::vector<BobUITrackDescriptor>> m_undoHistory;
    std::vector<std::vector<BobUITrackDescriptor>> m_redoHistory;
};

#endif // BOBUI_SESSION_BRIDGE_HPP
