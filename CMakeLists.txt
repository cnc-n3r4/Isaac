cmake_minimum_required(VERSION 3.16)
project(isaac_core VERSION 2.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Performance optimizations
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
if(NOT WIN32)
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -march=native -flto")
endif()

# Find Python and pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Try to find pybind11, if not found, use subdirectory or install it
find_package(pybind11 QUIET)
if(NOT pybind11_FOUND)
    # Try to find pybind11 via pip installed version
    execute_process(
      COMMAND ${Python_EXECUTABLE} -m pybind11 --cmakedir
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE pybind11_EXIT_CODE
    )
    
    if(pybind11_EXIT_CODE EQUAL 0)
        find_package(pybind11 REQUIRED HINTS ${pybind11_DIR})
    else()
  message(STATUS "pybind11 not found - building Python-only version")
        return()
    endif()
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/src)

# Check if source files exist before adding them
set(CORE_SOURCES)
set(SOURCE_FILES
    src/core/command_router.cpp
    src/core/tier_validator.cpp
    src/core/strategies.cpp
    src/adapters/shell_adapter.cpp
    src/bindings.cpp
)

foreach(SOURCE_FILE ${SOURCE_FILES})
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${SOURCE_FILE})
        list(APPEND CORE_SOURCES ${SOURCE_FILE})
    else()
        message(WARNING "Source file ${SOURCE_FILE} not found - skipping")
    endif()
endforeach()

# Only build if we have sources
if(CORE_SOURCES)
    # Create the Python extension module
    pybind11_add_module(isaac_core ${CORE_SOURCES})
    
    # Compiler-specific options
    target_compile_definitions(isaac_core PRIVATE VERSION_INFO=${PROJECT_VERSION})
  
    # Platform-specific optimizations
    if(WIN32)
target_compile_options(isaac_core PRIVATE /O2)
    else()
        target_compile_options(isaac_core PRIVATE -O3 -ffast-math)
    endif()
    
    message(STATUS "Building C++ core with ${list_length} source files")
else()
    message(WARNING "No C++ source files found - skipping C++ build")
endif()

# Installation
install(TARGETS isaac_core
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/lib/python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}/site-packages/isaac/
)