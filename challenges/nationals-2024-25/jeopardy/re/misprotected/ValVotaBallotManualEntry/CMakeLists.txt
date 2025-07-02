cmake_minimum_required(VERSION 3.19)

project(ValVotaBallotManualEntry LANGUAGES CXX)

# Ensure the compiler is Clang/LLVM
# The rest of this file assumes that the compiler is Clang
if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    message(FATAL_ERROR ${CMAKE_CXX_COMPILER_ID})
endif()

# Find Qt6 packages
find_package(Qt6 6.8 REQUIRED COMPONENTS Core Widgets Protobuf Grpc)
qt_standard_project_setup()

# Find and add VMProtect SDK
set(VMPROTECT_ROOT "C:/Program Files/VMProtect Ultimate")
set(VMPROTECT_INC  "${VMPROTECT_ROOT}/Include/C")
set(VMPROTECT_LIB  "${VMPROTECT_ROOT}/Lib/Windows/VMProtectSDK64.lib")

add_library(VMProtectSDK STATIC IMPORTED)
set_target_properties(VMProtectSDK PROPERTIES IMPORTED_LOCATION "${VMPROTECT_LIB}")

# Enable optimizations and strip symbols for releases
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O2 -march=x86-64-v3)
    add_link_options(-static-libgcc -static-libstdc++ -flto -Wl,-s,-Map,${CMAKE_BINARY_DIR}/ValVotaBallotManualEntry.map)
endif()

set(APP_RESOURCE_FILE "${CMAKE_CURRENT_SOURCE_DIR}/src/resources.rc")

qt_add_executable(ValVotaBallotManualEntry
    WIN32 MACOSX_BUNDLE
    ${APP_RESOURCE_FILE}
    src/main.cpp
    src/mainwindow.cpp
    src/mainwindow.h
    src/mainwindow.ui
    src/utils.cpp
    src/utils.h
    src/warningdialog.h src/warningdialog.cpp src/warningdialog.ui
    src/aboutdialog.h src/aboutdialog.cpp src/aboutdialog.ui
    src/authdialog.h src/authdialog.cpp src/authdialog.ui
)

qt_add_protobuf(ValVotaBallotManualEntry
    PROTO_FILES
        src/valvota.proto
)

qt_add_grpc(ValVotaBallotManualEntry CLIENT
    PROTO_FILES
        src/valvota.proto
)

target_include_directories(ValVotaBallotManualEntry PRIVATE "${VMPROTECT_INC}")

target_link_libraries(ValVotaBallotManualEntry
    PRIVATE
        Qt::Core
        Qt::Widgets
        Qt::Protobuf
        Qt::Grpc
        VMProtectSDK
)

include(GNUInstallDirs)

install(TARGETS ValVotaBallotManualEntry
    BUNDLE  DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

install(FILES configs/ValVotaBallotManualEntry.ini
    DESTINATION ${CMAKE_INSTALL_BINDIR}
)

qt_generate_deploy_app_script(
    TARGET ValVotaBallotManualEntry
    OUTPUT_SCRIPT deploy_script
    NO_UNSUPPORTED_PLATFORM_ERROR
)

install(SCRIPT ${deploy_script})
