#include "policy_model_path.hpp"

#include <cassert>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

int main() {
    const auto root = std::filesystem::temp_directory_path() /
        ("lite3-policy-path-" + std::to_string(static_cast<long long>(getpid())));
    const auto repo = root / "Lite-robot";
    const auto model = repo / "policy/ppo/policy.onnx";
    std::filesystem::create_directories(model.parent_path());
    std::ofstream(model) << "test";

    unsetenv("LITE3_POLICY_MODEL");
    assert(ResolveLite3PolicyModelPath(repo, repo / "build/lite3_xbox_control") ==
           std::filesystem::weakly_canonical(model).string());
    assert(ResolveLite3PolicyModelPath(root, repo / "build/lite3_xbox_control") ==
           std::filesystem::weakly_canonical(model).string());

    const auto configured = root / "configured.onnx";
    std::ofstream(configured) << "test";
    setenv("LITE3_POLICY_MODEL", configured.c_str(), 1);
    assert(ResolveLite3PolicyModelPath(root, {}) ==
           std::filesystem::weakly_canonical(configured).string());
    unsetenv("LITE3_POLICY_MODEL");

    std::filesystem::remove_all(root);
    std::cout << "policy_model_path_test PASS\n";
}
