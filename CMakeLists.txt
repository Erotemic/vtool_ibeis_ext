cmake_minimum_required(VERSION 3.5.0)

set(CMAKE_CXX_STANDARD 11)

#######################################
# Clang2 = Clang + OpenMP built for OSX Mavericks
# http://goo.gl/1Tg0Zj
if (APPLE)
    set(CMAKE_MACOSX_RPATH 1)
    message(STATUS "Detected APPLE system")
    SET(CLANG2 Off)
endif()

if (APPLE AND CLANG2)
    message(STATUS "Using clang2")
    set(CMAKE_C_COMPILER "clang2")
    set(CMAKE_CXX_COMPILER "clang2++")
endif()

#######################################
project(sver LANGUAGES C CXX) #### !!!!IMPORTANT!!!! THIS MUST BE DOWN HERE FOR CLANG2
#set(CMAKE_BUILD_TYPE "Release")

if (APPLE)
    #MacPorts
    message(STATUS "USING MACPORTS")
    # Fixme: newstyle include and link
    include_directories(/opt/local/include)
    link_directories(/opt/local/lib)
endif()

#######################################
if(APPLE AND CLANG2)
    # Add flags to support clang2
    message(STATUS "APPLE + CLANG2: Adding stdlib flags for clang")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -stdlib=libc++")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -lc++")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -lc++")
else()
    # TODO: this is gcc only, fix for clang
    #set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c++11")
    #set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
endif()

#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -stdlib=libc++")
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
#set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -lc++")
#set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -lc++")

# Setup basic python stuff and ensure we have skbuild
#list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_SOURCE_DIR}/CMake")
#include( skbuild-helpers )

#######################################


# OpenCV_ROOT_DIR=$HOME/.local
# OpenCV_ROOT_DIR=$HOME/.local python setup.py develop
#set(OpenCV_FIND_REQUIRED_COMPONENTS)
# ---- Robust OpenCV discovery (env + vcpkg) ----
if(DEFINED ENV{OpenCV_DIR} AND NOT OpenCV_DIR)
    set(OpenCV_DIR "$ENV{OpenCV_DIR}")
endif()
if(DEFINED ENV{OpenCV_ROOT} AND NOT OpenCV_ROOT)
    set(OpenCV_ROOT "$ENV{OpenCV_ROOT}")
endif()
if(DEFINED ENV{OpenCV_ROOT_DIR} AND NOT OpenCV_ROOT_DIR)
    set(OpenCV_ROOT_DIR "$ENV{OpenCV_ROOT_DIR}")
endif()

if(DEFINED ENV{VCPKG_ROOT} AND NOT OpenCV_DIR)
    if(DEFINED ENV{VCPKG_TARGET_TRIPLET})
        set(_vcpkg_triplet "$ENV{VCPKG_TARGET_TRIPLET}")
    elseif(WIN32)
        if(CMAKE_SIZEOF_VOID_P EQUAL 8)
            set(_vcpkg_triplet "x64-windows")
        else()
            set(_vcpkg_triplet "x86-windows")
        endif()
    endif()

    if(_vcpkg_triplet)
        set(_vcpkg_opencv_dir "$ENV{VCPKG_ROOT}/installed/${_vcpkg_triplet}/share/opencv4")
        set(OpenCV_DIR "${_vcpkg_opencv_dir}")
        if(NOT OpenCV_ROOT)
            set(OpenCV_ROOT "$ENV{VCPKG_ROOT}/installed/${_vcpkg_triplet}")
        endif()
    endif()
endif()

if(OpenCV_ROOT AND NOT CMAKE_PREFIX_PATH)
    set(CMAKE_PREFIX_PATH "${OpenCV_ROOT}")
endif()
# ---- End robust OpenCV discovery ----
find_package( OpenCV REQUIRED )
IF(OpenCV_FOUND)
  message(STATUS "Found OpenCV! ^_^")
  message(STATUS "OpenCV_FOUND = ${OpenCV_FOUND}")
  message(STATUS "OpenCV_INCLUDE_DIR = ${OpenCV_INCLUDE_DIR}")
  message(STATUS "OpenCV_LIBRARIES = ${OpenCV_LIBRARIES}")
  message(STATUS "OpenCV_LINK_DIRECTORIES = ${OpenCV_LINK_DIRECTORIES}")
  message(STATUS "OpenCV_ROOT_DIR = ${OpenCV_ROOT_DIR}")
ELSE()
  message(FATAL_ERROR "Missing OpenCV! x.x")
ENDIF()

#######################################
find_package(OpenMP)
IF(OPENMP_FOUND)
    message(STATUS "Found OpenMP! ^_^")
    # add flags for OpenMP
    #set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS} -fopenmp")
    #set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS} -fopenmp")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
    set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} ${OpenMP_C_FLAGS} ${OpenMP_SHARED_LINKER_FLAGS}")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_C_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
ELSE()
  message(STATUS "Missed OpenMP! x_x")
ENDIF()

option(ENABLE_GPROF Off)
IF(ENABLE_GPROF)
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pg")
    SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -pg")
    SET(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -pg")
ENDIF()

#######################################
set(SOURCE_FILES
    cppsrc/sver.cpp)

message(STATUS "OpenMP_SHARED_LINKER_FLAGS = ${OpenMP_SHARED_LINKER_FLAGS}")
message(STATUS "OpenMP_EXE_LINKER_FLAGS = ${OpenMP_EXE_LINKER_FLAGS}")
message(STATUS "OpenCV_INCLUDE_DIR = ${OpenCV_INCLUDE_DIR}")
message(STATUS "OpenCV_LIBRARIES = ${OpenCV_LIBRARIES}")
set(_opencv_includes "${OpenCV_INCLUDE_DIRS}")
if(NOT _opencv_includes)
    set(_opencv_includes "${OpenCV_INCLUDE_DIR}")
endif()

# Use MODULE instead of SHARED for windows
add_library(sver MODULE ${SOURCE_FILES})



set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
#if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC")
#    # Set the DLLEXPORT variable to export symbols
#    target_compile_definitions(sver PRIVATE HESAFF_WIN_EXPORT)
#endif()

target_include_directories(sver PRIVATE ${_opencv_includes})

#######################################
target_link_libraries(sver PRIVATE ${OpenCV_LIBRARIES})
# I think: An install target is required so scikit-build knows where the binaries are
# https://github.com/scikit-build/scikit-build/issues/434
# Note: if the target is not referenced by package_data in setup.py then the
# lib will be installed as a data file and not a package file.
#install(TARGETS sver LIBRARY DESTINATION "vtool_ibeis_ext")
install(TARGETS sver
    RUNTIME DESTINATION vtool_ibeis_ext/lib
    LIBRARY DESTINATION vtool_ibeis_ext/lib
    ARCHIVE DESTINATION vtool_ibeis_ext/lib
)
