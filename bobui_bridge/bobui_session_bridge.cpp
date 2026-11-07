#include "bobui_session_bridge.hpp"
#include <fstream>
#include <sstream>
#include <iostream>

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

bool BobUISessionBridge::saveCheckpoint(const std::string& name, const std::vector<BobUITrackDescriptor>& tracks) {
    m_checkpoints[name] = tracks;
    m_undoHistory.push_back(tracks);
    return true;
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::restoreCheckpoint(const std::string& name) {
    auto it = m_checkpoints.find(name);
    if (it != m_checkpoints.end()) {
        return it->second;
    }
    return {};
}

std::vector<BobUITrackDescriptor> BobUISessionBridge::undoLastAction() {
    if (m_undoHistory.size() > 1) {
        m_undoHistory.pop_back(); // Remove current
        return m_undoHistory.back();
    }
    return {};
}
