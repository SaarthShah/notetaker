#include "crow.h"
#include "ZoomSDK.h" // Include your Zoom SDK headers

// Initialize the Zoom SDK
bool initializeZoomSDK() {
    ZOOM_SDK_NAMESPACE::InitParam initParam;
    initParam.strWebDomain = "https://zoom.us";
    initParam.strSupportUrl = "https://zoom.us";
    initParam.emLanguageID = ZOOM_SDK_NAMESPACE::LANGUAGE_English;
    initParam.enableLogByDefault = true;
    initParam.enableGenerateDump = true;
    ZOOM_SDK_NAMESPACE::SDKError err = ZOOM_SDK_NAMESPACE::InitSDK(initParam);
    return err == ZOOM_SDK_NAMESPACE::SDKERR_SUCCESS;
}

// Start a meeting
bool startMeeting() {
    ZOOM_SDK_NAMESPACE::StartParam startParam;
    startParam.userType = ZOOM_SDK_NAMESPACE::SDK_UT_NORMALUSER;
    startParam.param.normaluserStart.isVideoOff = false;
    startParam.param.normaluserStart.isAudioOff = false;
    ZOOM_SDK_NAMESPACE::IMeetingService* m_pMeetingService = SDKInterfaceWrap::GetInst().GetMeetingService();
    ZOOM_SDK_NAMESPACE::SDKError err = m_pMeetingService->Start(startParam);
    return err == ZOOM_SDK_NAMESPACE::SDKERR_SUCCESS;
}

// Join a meeting
bool joinMeeting(const std::string& meetingNumber, const std::string& userName, const std::string& password) {
    ZOOM_SDK_NAMESPACE::JoinParam joinParam;
    joinParam.userType = ZOOM_SDK_NAMESPACE::SDK_UT_WITHOUT_LOGIN;
    ZOOM_SDK_NAMESPACE::JoinParam4WithoutLogin& withoutloginParam = joinParam.param.withoutloginuserJoin;
    withoutloginParam.meetingNumber = std::stoull(meetingNumber);
    withoutloginParam.userName = userName.c_str();
    withoutloginParam.psw = password.c_str();
    ZOOM_SDK_NAMESPACE::IMeetingService* m_pMeetingService = SDKInterfaceWrap::GetInst().GetMeetingService();
    ZOOM_SDK_NAMESPACE::SDKError err = m_pMeetingService->Join(joinParam);
    return err == ZOOM_SDK_NAMESPACE::SDKERR_SUCCESS;
}

// Leave a meeting
bool leaveMeeting() {
    ZOOM_SDK_NAMESPACE::IMeetingService* m_pMeetingService = SDKInterfaceWrap::GetInst().GetMeetingService();
    ZOOM_SDK_NAMESPACE::SDKError err = m_pMeetingService->Leave(ZOOM_SDK_NAMESPACE::LEAVE_MEETING);
    return err == ZOOM_SDK_NAMESPACE::SDKERR_SUCCESS;
}

int main() {
    if (!initializeZoomSDK()) {
        std::cerr << "Failed to initialize Zoom SDK" << std::endl;
        return -1;
    }

    crow::SimpleApp app;

    CROW_ROUTE(app, "/start")
    ([]() {
        if (startMeeting()) {
            return crow::response(200, "Meeting started successfully");
        } else {
            return crow::response(500, "Failed to start meeting");
        }
    });

    CROW_ROUTE(app, "/join")
    .methods("POST"_method)
    ([](const crow::request& req) {
        auto body = crow::json::load(req.body);
        if (!body) {
            return crow::response(400, "Invalid JSON");
        }
        std::string meetingNumber = body["meetingNumber"].s();
        std::string userName = body["userName"].s();
        std::string password = body["password"].s();

        if (joinMeeting(meetingNumber, userName, password)) {
            return crow::response(200, "Joined meeting successfully");
        } else {
            return crow::response(500, "Failed to join meeting");
        }
    });

    CROW_ROUTE(app, "/leave")
    ([]() {
        if (leaveMeeting()) {
            return crow::response(200, "Left meeting successfully");
        } else {
            return crow::response(500, "Failed to leave meeting");
        }
    });

    app.port(18080).multithreaded().run();
}