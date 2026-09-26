#include "local_xbox_state_machine.hpp"

#include <cassert>
#include <iostream>

MotionStateFeedback StateBase::msfb_=MotionStateFeedback();

class FakeInput final : public UserCommandInterface {
public:
    void Start() override { ++starts; }
    void Stop() override { ++stops; }
    UserCommand GetUserCommand() override { return command; }
    void SetMotionStateFeedback(const MotionStateFeedback& value) override { msfb_=value; }
    bool IsConnected() const override { return connected; }
    UserCommand command{};
    bool connected=true;
    int starts=0,stops=0;
};

class FakeRobot final : public RobotInterface {
public:
    FakeRobot():RobotInterface("fake",12) { joint_cmd_=MatXf::Zero(12,5); }
    void Start() override { ++starts; }
    void Stop() override { ++stops; }
    bool AcquireControl() override { ++acquires; requested=true; return fresh; }
    void ReleaseControl() override { ++releases; gate=false; requested=false; }
    bool IsControlRequestSent() const override { return requested; }
    bool IsFeedbackFresh() const override { return fresh; }
    void SetJointCommandEnabled(bool enabled) override { if(!enabled) gate=false; }
    bool JointCommandsEnabled() const override { return gate; }
    double GetInterfaceTimeStamp() override { return stamp; }
    VecXf GetJointPosition() override { return VecXf::Zero(12); }
    VecXf GetJointVelocity() override { return VecXf::Zero(12); }
    VecXf GetJointTorque() override { return VecXf::Zero(12); }
    Vec3f GetImuRpy() override { return Vec3f::Zero(); }
    Vec3f GetImuAcc() override { return Vec3f(0,0,gravity); }
    Vec3f GetImuOmega() override { return Vec3f::Zero(); }
    VecXf GetContactForce() override { return VecXf::Zero(4); }
    void SetJointCommand(Eigen::Matrix<float, Eigen::Dynamic, 5> input) override { if(gate) joint_cmd_=std::move(input); }
    bool fresh=true,requested=false,gate=false;
    double stamp=1.0;
    int starts=0,stops=0,acquires=0,releases=0;
protected:
    bool OpenLocalXboxControl(const std::shared_ptr<const LocalXboxControlPermit>& permit) override {
        if(!requested || !fresh || !permit || !permit->Valid()) return false;
        gate=true; return true;
    }
};

class FakeState final : public StateBase {
public:
    FakeState(StateName self,std::shared_ptr<ControllerData> data)
        :StateBase(RobotType::Lite3,"fake",std::move(data)),self(self),next(self) {}
    void OnEnter() override { ++enters; }
    void OnExit() override { ++exits; }
    void Run() override { ++runs; }
    bool LoseControlJudge() override { return lose; }
    StateName GetNextStateName() override { return next; }
    StateName self,next;
    bool lose=false;
    int enters=0,exits=0,runs=0;
};

int main() {
    auto robot=std::make_shared<FakeRobot>();
    auto input=std::make_shared<FakeInput>();
    auto data=std::make_shared<ControllerData>();
    data->ri_ptr=robot; data->uc_ptr=input;
    auto idle=std::make_shared<FakeState>(kIdle,data);
    auto stand=std::make_shared<FakeState>(kStandUp,data);
    auto rl=std::make_shared<FakeState>(kRLControl,data);
    auto damping=std::make_shared<FakeState>(kJointDamping,data);

    LocalXboxStateMachine runtime(robot,input,idle,stand,rl,damping);
    assert(robot->acquires==0 && !robot->gate && idle->enters==1);

    idle->next=kStandUp; // Xbox LB edge accepted by the real IdleState.
    assert(runtime.ProcessOnce());
    assert(runtime.CurrentState()==kStandUp);
    assert(robot->acquires==1 && robot->gate);

    robot->stamp+=1.0; stand->next=kRLControl;
    assert(runtime.ProcessOnce());
    assert(runtime.CurrentState()==kRLControl && robot->acquires==1);

    robot->stamp+=1.0; input->connected=false;
    assert(runtime.ProcessOnce());
    assert(runtime.CurrentState()==kJointDamping);

    robot->stamp+=1.0; damping->next=kIdle;
    assert(!runtime.ProcessOnce());
    assert(!robot->gate && !robot->requested && robot->releases>=1);
    assert(input->stops==1 && robot->stops==1);
    std::cout<<"local_xbox_runtime_test PASS\n";
}
