#include <arpa/inet.h>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <iomanip>
#include <map>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

int main() {
  const int fd = socket(AF_INET, SOCK_DGRAM, 0);
  sockaddr_in local{};
  local.sin_family = AF_INET;
  local.sin_addr.s_addr = htonl(INADDR_ANY);
  local.sin_port = htons(43897);
  if (bind(fd, reinterpret_cast<sockaddr *>(&local), sizeof(local)) != 0) {
    perror("bind"); return 1;
  }
  timeval timeout{10, 0};
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
  std::map<uint32_t, std::pair<size_t, size_t>> types;
  std::map<uint32_t, std::vector<uint8_t>> samples;
  std::array<uint8_t, 2048> packet{};
  for (int i = 0; i < 500; ++i) {
    const auto n = recv(fd, packet.data(), packet.size(), 0);
    if (n <= 0) break;
    uint32_t code = 0, size = 0;
    if (n >= 12) { std::memcpy(&code, packet.data(), 4); std::memcpy(&size, packet.data() + 8, 4); }
    auto &entry = types[code]; entry.first++; entry.second = static_cast<size_t>(n);
    if (!samples.contains(code)) samples[code] = {packet.begin(), packet.begin() + n};
  }
  close(fd);
  for (const auto &[code, value] : types) {
    std::cout << "code=0x" << std::hex << code << std::dec
              << " datagrams=" << value.first << " bytes=" << value.second << '\n';
    for (size_t i = 0; i < samples[code].size(); ++i) {
      if (i % 16 == 0) std::cout << "  ";
      std::cout << std::hex << std::setw(2) << std::setfill('0')
                << static_cast<unsigned>(samples[code][i]) << ' ';
      if (i % 16 == 15 || i + 1 == samples[code].size()) std::cout << std::dec << '\n';
    }
  }
}
