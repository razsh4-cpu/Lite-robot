#pragma once
#include "robot_types.h"
#include <functional>
#include <memory>
#include <string>
// Inert test seam. Deliberately no RobotStateInit operation.
class MotionSdkTransport {
public:
    using Feedback = std::function<void(const RobotData&)>;
    virtual ~MotionSdkTransport() = default;
    virtual void StartFeedback(Feedback callback) = 0;
    virtual void RequestOwnership(unsigned mode) = 0;
    virtual void SendJoints(RobotCmd& command) = 0;
};
std::shared_ptr<MotionSdkTransport> MakeMotionSdkTransport(const std::string& ip, int port);
