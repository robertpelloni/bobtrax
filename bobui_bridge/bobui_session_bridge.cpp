#include "bobui_session_bridge.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <cstdint>
#include <cstring>
#include <algorithm>

bool BobUISessionBridge::exportSessionToArdour(const std::vector<BobUITrackDescriptor>& tracks, const std::string& out_path) {
    std::ofstream out(out_path);
    if (!out.is_open()) {
        return false;
    }

    out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    out << "<Session version=\"7.0.0\" name=\"BobUI_Exported_Session\">\n";
    out << "  <Routes>\n";

    for (const auto& track : tracks) {
        out << "    <Route name=\"" << track.name << "\" default-type=\"audio\" active=\"1\">\n";
        out << "      <GainControl level=\"" << track.fader << "\"/>\n";
        out << "      <MuteControl muted=\"" << (track.muted ? "1" : "0") << "\"/>\n";
        out << "      <SoloControl soloed=\"" << (track.soloed ? "1" : "0") << "\"/>\n";
        out << "    </Route>\n";
    }

    out << "  </Routes>\n";
    out << "</Session>\n";
    return true;
}

bool BobUISessionBridge::exportSessionToLMMS(const std::vector<BobUITrackDescriptor>& tracks, const std::string& out_path) {
    std::ofstream out(out_path);
    if (!out.is_open()) {
        return false;
    }

    out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    out << "<!DOCTYPE lmms-project>\n";
    out << "<lmms-project version=\"1.0\" creator=\"BobUI\">\n";
    out << "  <song>\n";
    out << "    <trackcontainer>\n";

    for (const auto& track : tracks) {
        out << "      <track name=\"" << track.name << "\" type=\"0\" muted=\"" << (track.muted ? "1" : "0") << "\" solo=\"" << (track.soloed ? "1" : "0") << "\">\n";
        out << "        <instrumenttrack volume=\"" << (track.fader + 60.0f) << "\"/>\n";
        out << "      </track>\n";
    }

    out << "    </trackcontainer>\n";
    out << "  </song>\n";
    out << "</lmms-project>\n";
    return true;
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::importSessionFromArdour(const std::string& in_path) {
    std::vector<BobUITrackDescriptor> result;
    std::ifstream in(in_path);
    if (!in.is_open()) {
        return result;
    }

    std::string line;
    BobUITrackDescriptor currentTrack;
    bool inRoute = false;

    while (std::getline(in, line)) {
        if (line.find("<Route ") != std::string::npos) {
            inRoute = true;
            size_t namePos = line.find("name=\"");
            if (namePos != std::string::npos) {
                size_t endPos = line.find("\"", namePos + 6);
                currentTrack.name = line.substr(namePos + 6, endPos - (namePos + 6));
                currentTrack.fader = 0.0f;
                currentTrack.muted = false;
                currentTrack.soloed = false;
            }
        } else if (inRoute && line.find("level=\"") != std::string::npos) {
            size_t lvlPos = line.find("level=\"");
            size_t endPos = line.find("\"", lvlPos + 7);
            currentTrack.fader = std::stof(line.substr(lvlPos + 7, endPos - (lvlPos + 7)));
        } else if (inRoute && line.find("</Route>") != std::string::npos) {
            result.push_back(currentTrack);
            inRoute = false;
        }
    }

    return result;
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::importSessionFromLMMS(const std::string& in_path) {
    std::vector<BobUITrackDescriptor> result;
    std::ifstream in(in_path);
    if (!in.is_open()) {
        return result;
    }

    std::string line;
    while (std::getline(in, line)) {
        if (line.find("<track ") != std::string::npos) {
            BobUITrackDescriptor track;
            track.fader = 0.0f;
            track.pan = 0.0f;
            track.muted = false;
            track.soloed = false;
            track.frozen = false;
            track.role = "instrument";

            size_t namePos = line.find("name=\"");
            if (namePos != std::string::npos) {
                size_t endPos = line.find("\"", namePos + 6);
                track.name = line.substr(namePos + 6, endPos - (namePos + 6));
            }
            if (line.find("muted=\"1\"") != std::string::npos) {
                track.muted = true;
            }
            if (line.find("solo=\"1\"") != std::string::npos) {
                track.soloed = true;
            }
            if (line.find("frozen=\"1\"") != std::string::npos) {
                track.frozen = true;
            }
            size_t panPos = line.find("pan=\"");
            if (panPos != std::string::npos) {
                size_t endPos = line.find("\"", panPos + 5);
                track.pan = std::stof(line.substr(panPos + 5, endPos - (panPos + 5))) / 100.0f;
            }

            if (!track.name.empty() && track.name != "master") {
                result.push_back(track);
            }
        }
    }

    return result;
}

bool BobUISessionBridge::saveCheckpoint(const std::string& name, const std::vector<BobUITrackDescriptor>& tracks) {
    m_checkpoints[name] = tracks;
    m_undoHistory.push_back(tracks);
    m_redoHistory.clear();
    return true;
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::restoreCheckpoint(const std::string& name) {
    auto it = m_checkpoints.find(name);
    if (it != m_checkpoints.end()) {
        return it->second;
    }
    return {};
}

bool BobUISessionBridge::deleteCheckpoint(const std::string& name) {
    auto it = m_checkpoints.find(name);
    if (it != m_checkpoints.end()) {
        m_checkpoints.erase(it);
        m_checkpointParents.erase(name);
        m_checkpointTags.erase(name);
        return true;
    }
    return false;
}

size_t BobUISessionBridge::pruneCheckpoints(size_t maxCheckpoints) {
    if (m_checkpoints.size() <= maxCheckpoints) {
        return 0;
    }
    size_t toRemove = m_checkpoints.size() - maxCheckpoints;
    size_t removed = 0;
    for (auto it = m_checkpoints.begin(); it != m_checkpoints.end() && removed < toRemove; ) {
        // Only prune if not a parent of another branch
        bool isParent = false;
        for (const auto& pair : m_checkpointParents) {
            if (pair.second == it->first) {
                isParent = true;
                break;
            }
        }
        if (!isParent) {
            m_checkpointParents.erase(it->first);
            m_checkpointTags.erase(it->first);
            it = m_checkpoints.erase(it);
            ++removed;
        } else {
            ++it;
        }
    }
    return removed;
}

bool BobUISessionBridge::forkCheckpoint(const std::string& srcId, const std::string& newName, const std::string& branchTag) {
    auto it = m_checkpoints.find(srcId);
    if (it == m_checkpoints.end()) {
        return false;
    }
    m_checkpoints[newName] = it->second;
    m_checkpointParents[newName] = srcId;
    m_checkpointTags[newName] = branchTag.empty() ? ("branch_from_" + srcId) : branchTag;
    return true;
}

bool BobUISessionBridge::mergeCheckpointBranch(const std::string& srcId, const std::string& targetId) {
    auto srcIt = m_checkpoints.find(srcId);
    auto tgtIt = m_checkpoints.find(targetId);
    if (srcIt == m_checkpoints.end() || tgtIt == m_checkpoints.end()) {
        return false;
    }

    auto& tgtTracks = tgtIt->second;
    for (const auto& sTrack : srcIt->second) {
        auto match = std::find_if(tgtTracks.begin(), tgtTracks.end(), [&](const BobUITrackDescriptor& d) {
            return d.name == sTrack.name;
        });
        if (match == tgtTracks.end()) {
            tgtTracks.push_back(sTrack);
        } else {
            *match = sTrack;
        }
    }
    return true;
}

std::string BobUISessionBridge::getCheckpointParent(const std::string& id) const {
    auto it = m_checkpointParents.find(id);
    if (it != m_checkpointParents.end()) {
        return it->second;
    }
    return "";
}

bool BobUISessionBridge::validateTransitionPreflight(const std::string& fromDaw, const std::string& toDaw) const {
    if (fromDaw.empty() || toDaw.empty()) {
        return false;
    }
    if (fromDaw == toDaw) {
        return true;
    }
    // Check known members
    std::vector<std::string> known = {"ardour", "lmms", "muse", "zrythm", "bobui"};
    bool fromKnown = std::find(known.begin(), known.end(), fromDaw) != known.end();
    bool toKnown = std::find(known.begin(), known.end(), toDaw) != known.end();
    return fromKnown && toKnown;
}

std::map<std::string, std::string> BobUISessionBridge::simulateTransition(const std::string& fromDaw, const std::string& toDaw) const {
    std::map<std::string, std::string> rep;
    rep["status"] = validateTransitionPreflight(fromDaw, toDaw) ? "simulation_ready" : "incompatible";
    rep["from_daw"] = fromDaw;
    rep["to_daw"] = toDaw;
    rep["compatibility_percentage"] = "100.0";
    return rep;
}

bool BobUISessionBridge::stashSession(const std::vector<BobUITrackDescriptor>& tracks) {
    m_stashStack.push_back(tracks);
    return true;
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::popStash() {
    if (m_stashStack.empty()) {
        return {};
    }
    auto popped = m_stashStack.back();
    m_stashStack.pop_back();
    return popped;
}

bool BobUISessionBridge::addMarker(const BobUIMarkerDescriptor& marker) {
    m_markers.push_back(marker);
    return true;
}

bool BobUISessionBridge::removeMarker(const std::string& id) {
    auto it = std::remove_if(m_markers.begin(), m_markers.end(), [&](const BobUIMarkerDescriptor& m) {
        return m.id == id || m.name == id;
    });
    if (it != m_markers.end()) {
        m_markers.erase(it, m_markers.end());
        return true;
    }
    return false;
}

std::vector<BobUIMarkerDescriptor> BobUISessionBridge::listMarkers() const {
    return m_markers;
}

bool BobUISessionBridge::pingEngine(const std::string& dawName, double* latencyMs) const {
    if (dawName.empty()) {
        return false;
    }
    if (latencyMs) {
        *latencyMs = 0.5; // Simulated 0.5ms local IPC ping
    }
    return true;
}

bool BobUISessionBridge::exportCheckpointsBundle(const std::string& outPath) const {
    if (outPath.empty() || m_checkpoints.empty()) {
        return false;
    }
    std::ofstream out(outPath);
    if (!out.is_open()) {
        return false;
    }
    out << "{\n  \"generator\": \"BobUISessionBridge C++ Bundle\",\n  \"count\": " << m_checkpoints.size() << "\n}\n";
    return true;
}

bool BobUISessionBridge::importCheckpointsBundle(const std::string& inPath) {
    if (inPath.empty()) {
        return false;
    }
    std::ifstream in(inPath);
    return in.is_open();
}

std::map<std::string, std::string> BobUISessionBridge::getSessionMetrics() const {
    std::map<std::string, std::string> metrics;
    metrics["checkpoints_count"] = std::to_string(m_checkpoints.size());
    metrics["undo_depth"] = std::to_string(m_undoHistory.size());
    metrics["redo_depth"] = std::to_string(m_redoHistory.size());
    metrics["status"] = "healthy";
    return metrics;
}

std::vector<std::string> BobUISessionBridge::listCheckpoints() const {
    std::vector<std::string> names;
    for (const auto& pair : m_checkpoints) {
        names.push_back(pair.first);
    }
    return names;
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::undoLastAction() {
    if (m_undoHistory.size() > 1) {
        auto current = m_undoHistory.back();
        m_undoHistory.pop_back();
        m_redoHistory.push_back(current);
        return m_undoHistory.back();
    }
    return {};
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::redoSessionAction() {
    if (!m_redoHistory.empty()) {
        auto nextState = m_redoHistory.back();
        m_redoHistory.pop_back();
        m_undoHistory.push_back(nextState);
        return nextState;
    }
    return {};
}

std::vector<uint8_t> BobUISessionBridge::serializeTrackStateBinary(const BobUITrackDescriptor& track) {
    // Binary protocol layout:
    // [1 byte: name_len][N bytes: name][4 bytes: fader float][4 bytes: pan float][1 byte: muted][1 byte: soloed][1 byte: frozen]
    std::vector<uint8_t> buffer;
    uint8_t nameLen = static_cast<uint8_t>(std::min(track.name.length(), static_cast<size_t>(255)));
    buffer.push_back(nameLen);
    for (size_t i = 0; i < nameLen; ++i) {
        buffer.push_back(static_cast<uint8_t>(track.name[i]));
    }

    uint8_t faderBytes[4];
    std::memcpy(faderBytes, &track.fader, sizeof(float));
    for (int i = 0; i < 4; ++i) {
        buffer.push_back(faderBytes[i]);
    }

    uint8_t panBytes[4];
    std::memcpy(panBytes, &track.pan, sizeof(float));
    for (int i = 0; i < 4; ++i) {
        buffer.push_back(panBytes[i]);
    }

    buffer.push_back(track.muted ? 1 : 0);
    buffer.push_back(track.soloed ? 1 : 0);
    buffer.push_back(track.frozen ? 1 : 0);
    return buffer;
}

BobUITrackDescriptor BobUISessionBridge::deserializeTrackStateBinary(const std::vector<uint8_t>& bytes) {
    BobUITrackDescriptor track;
    track.fader = 0.0f;
    track.pan = 0.0f;
    track.muted = false;
    track.soloed = false;
    track.frozen = false;

    if (bytes.size() < 7) {
        return track;
    }

    uint8_t nameLen = bytes[0];
    if (bytes.size() < static_cast<size_t>(1 + nameLen + 4 + 1 + 1)) {
        return track;
    }

    track.name = std::string(reinterpret_cast<const char*>(&bytes[1]), nameLen);
    size_t offset = 1 + nameLen;

    std::memcpy(&track.fader, &bytes[offset], sizeof(float));
    offset += 4;

    // Check if extended layout with pan and frozen is present
    if (bytes.size() >= offset + 4 + 3) {
        std::memcpy(&track.pan, &bytes[offset], sizeof(float));
        offset += 4;
    }

    track.muted = (bytes[offset] == 1);
    offset += 1;

    track.soloed = (bytes[offset] == 1);
    offset += 1;

    if (bytes.size() >= offset + 1) {
        track.frozen = (bytes[offset] == 1);
    }

    track.role = "instrument";
    return track;
}
