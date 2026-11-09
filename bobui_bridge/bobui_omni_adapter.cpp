#include "bobui_omni_adapter.hpp"
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <cstring>
#include <iostream>
#include <sstream>

BobUIOmniAdapter::BobUIOmniAdapter(const std::string& socket_path)
    : m_socketPath(socket_path), m_socketFd(-1) {}

BobUIOmniAdapter::~BobUIOmniAdapter() {
    disconnect();
}

bool BobUIOmniAdapter::connect() {
    if (m_socketFd >= 0) {
        return true;
    }

    m_socketFd = socket(AF_UNIX, SOCK_STREAM, 0);
    if (m_socketFd < 0) {
        return false;
    }

    struct sockaddr_un addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    std::strncpy(addr.sun_path, m_socketPath.c_str(), sizeof(addr.sun_path) - 1);

    if (::connect(m_socketFd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        close(m_socketFd);
        m_socketFd = -1;
        return false;
    }

    return true;
}

void BobUIOmniAdapter::disconnect() {
    if (m_socketFd >= 0) {
        close(m_socketFd);
        m_socketFd = -1;
    }
}

bool BobUIOmniAdapter::isConnected() const {
    return m_socketFd >= 0;
}

bool BobUIOmniAdapter::setParameter(const std::string& track_id, const std::string& plugin_id,
                                    const std::string& param_name, float value) {
    if (!connect()) {
        return false;
    }

    std::string key = track_id + ":" + plugin_id + ":" + param_name;
    std::string cmd = "SET " + key + " " + std::to_string(value) + "\n";

    ssize_t sent = send(m_socketFd, cmd.c_str(), cmd.length(), 0);
    if (sent < 0) {
        disconnect();
        return false;
    }

    char buf[256];
    ssize_t received = recv(m_socketFd, buf, sizeof(buf) - 1, 0);
    if (received > 0) {
        buf[received] = '\0';
        return true;
    }

    return false;
}

bool BobUIOmniAdapter::bulkSyncTracksBinary(const std::vector<BobUITrackDescriptor>& tracks) {
    if (tracks.empty()) {
        return true;
    }
    if (!connect()) {
        return false;
    }

    std::ostringstream ss;
    ss << "BULK_SYNC ";
    for (size_t i = 0; i < tracks.size(); ++i) {
        if (i > 0) ss << ";";
        ss << tracks[i].name << ":fader=" << tracks[i].fader << ",pan=" << tracks[i].pan;
    }
    ss << "\n";

    std::string cmd = ss.str();
    ssize_t sent = send(m_socketFd, cmd.c_str(), cmd.length(), 0);
    if (sent < 0) {
        disconnect();
        return false;
    }

    char buf[512];
    ssize_t received = recv(m_socketFd, buf, sizeof(buf) - 1, 0);
    if (received > 0) {
        return true;
    }
    return false;
}

std::map<std::string, float> BobUIOmniAdapter::getAllParameters() {
    std::map<std::string, float> result;
    if (!connect()) {
        return result;
    }

    std::string cmd = "GET_ALL\n";
    if (send(m_socketFd, cmd.c_str(), cmd.length(), 0) < 0) {
        disconnect();
        return result;
    }

    char buf[1024];
    ssize_t received = recv(m_socketFd, buf, sizeof(buf) - 1, 0);
    if (received > 0) {
        buf[received] = '\0';
        // Parse simple responses
    }

    return result;
}
