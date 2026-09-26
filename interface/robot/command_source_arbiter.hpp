#pragma once

#include <cerrno>
#include <fcntl.h>
#include <string>
#include <sys/file.h>
#include <unistd.h>

enum class CommandSource {
    None,
    Autonomy,
    LocalXbox,
    LaptopXbox,
};

inline const char* CommandSourceName(CommandSource source) {
    switch(source) {
        case CommandSource::Autonomy: return "AUTONOMY";
        case CommandSource::LocalXbox: return "LOCAL_XBOX";
        case CommandSource::LaptopXbox: return "LAPTOP_XBOX";
        default: return "NONE";
    }
}

// Process-lifetime exclusive lease. Every production command source uses the
// same lock protocol; adding Nav2/patrol requires no Xbox-specific changes.
// Acquisition is non-preemptive: a new source can never steal control.
class CommandSourceLease final {
public:
    explicit CommandSourceLease(
        std::string lock_path="/run/lite3-control/owner.lock")
        : lock_path_(std::move(lock_path)) {}

    ~CommandSourceLease() { Release(); }
    CommandSourceLease(const CommandSourceLease&)=delete;
    CommandSourceLease& operator=(const CommandSourceLease&)=delete;

    bool TryAcquire(CommandSource source) {
        if(source==CommandSource::None || fd_>=0) return false;
        const int fd=open(lock_path_.c_str(),O_RDWR|O_CREAT|O_CLOEXEC,0664);
        if(fd<0) return false;
        if(flock(fd,LOCK_EX|LOCK_NB)!=0) { close(fd); return false; }
        fd_=fd;
        source_=source;
        WriteState(CommandSourceName(source_));
        return true;
    }

    void Release() {
        if(fd_<0) return;
        WriteState("NONE");
        flock(fd_,LOCK_UN);
        close(fd_);
        fd_=-1;
        source_=CommandSource::None;
    }

    bool Held() const { return fd_>=0; }
    CommandSource Source() const { return source_; }

private:
    void WriteState(const char* state) {
        if(fd_<0) return;
        const std::string text=std::string("COMMAND_SOURCE=")+state+
            "\nPID="+std::to_string(static_cast<long long>(getpid()))+"\n";
        if(ftruncate(fd_,0)!=0) return;
        if(lseek(fd_,0,SEEK_SET)<0) return;
        const char* p=text.data();
        size_t remaining=text.size();
        while(remaining) {
            const ssize_t n=write(fd_,p,remaining);
            if(n<0) { if(errno==EINTR) continue; break; }
            p+=n; remaining-=static_cast<size_t>(n);
        }
        fsync(fd_);
    }

    std::string lock_path_;
    int fd_{-1};
    CommandSource source_{CommandSource::None};
};
