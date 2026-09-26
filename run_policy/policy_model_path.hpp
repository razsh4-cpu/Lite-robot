#pragma once

#include <cstdlib>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>

#include <limits.h>
#include <unistd.h>

inline std::filesystem::path Lite3ExecutablePath() {
    char buffer[PATH_MAX + 1]{};
    const ssize_t size = readlink("/proc/self/exe", buffer, PATH_MAX);
    if (size <= 0) return {};
    buffer[size] = '\0';
    return std::filesystem::path(buffer);
}

inline std::string ResolveLite3PolicyModelPath(
    const std::filesystem::path& working_directory =
        std::filesystem::current_path(),
    const std::filesystem::path& executable = Lite3ExecutablePath()) {
    std::vector<std::filesystem::path> candidates;
    if (const char* configured = std::getenv("LITE3_POLICY_MODEL");
        configured && *configured)
        candidates.emplace_back(configured);

    candidates.push_back(working_directory / "policy/ppo/policy.onnx");
    if (!executable.empty())
        candidates.push_back(
            executable.parent_path().parent_path() / "policy/ppo/policy.onnx");
    candidates.push_back(working_directory / "../policy/ppo/policy.onnx");

    for (const auto& candidate : candidates) {
        std::error_code error;
        if (std::filesystem::is_regular_file(candidate, error))
            return std::filesystem::weakly_canonical(candidate, error).string();
    }

    std::string message = "Lite3 policy.onnx not found; checked:";
    for (const auto& candidate : candidates)
        message += " " + candidate.lexically_normal().string();
    throw std::runtime_error(message);
}
