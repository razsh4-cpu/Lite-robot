#include "hardware_interface.hpp"
#include "sender.h"
#include "receiver.h"
namespace {
class VendorTransport final : public MotionSdkTransport {
    std::string ip_;
    int port_;
    std::unique_ptr<Sender> sender_;
    bool started_{false};
public:
    VendorTransport(std::string ip, int port): ip_(std::move(ip)), port_(port) {}
    void StartFeedback(Feedback callback) override {
        if (started_) return;
        // Bundled Receiver constructor already calls StartWork(). Its worker
        // detaches and has no stop/join API. Retain receiver until process exit;
        // the callback holds only a weak reference to our feedback store.
        auto* receiver = new Receiver();
        receiver->RegisterCallBack([receiver, callback=std::move(callback)](int code) {
            if (code == 0x0906) callback(receiver->GetState());
        });
        started_=true;
    }
    void RequestOwnership(unsigned mode) override {
        if (!sender_) sender_=std::make_unique<Sender>(ip_,port_);
        sender_->ControlGet(mode);
    }
    void SendJoints(RobotCmd& command) override {
        if (!sender_) throw std::logic_error("SendJoints before ownership request");
        sender_->SendCmd(command);
    }
};
}
std::shared_ptr<MotionSdkTransport> MakeMotionSdkTransport(const std::string& ip, int port) {
    return std::make_shared<VendorTransport>(ip,port);
}
HardwareInterface::HardwareInterface(const std::string& name, std::string ip, int port)
    : HardwareInterface(name, MakeMotionSdkTransport(ip,port)) {}
