cmake_minimum_required(VERSION 2.8.3)
project(combinatory_input)

find_package(catkin REQUIRED COMPONENTS)

include_directories(
    ${catkin_INCLUDE_DIRS}
)

catkin_package(
    LIBRARIES combinatory_input
    CATKIN_DEPENDS combinatory_processing
)

catkin_python_setup()