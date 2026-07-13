# src/memo/CMakeLists.txt
cmake_minimum_required(VERSION 3.20)

file(GLOB_RECURSE MEMO_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/*.c"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cc"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cxx"
  "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
)

# The live x64 memo backend is the existing DTX MemoStore (memostore.cpp).
# x64_memo_store.cpp was the experimental second OO backend and must not be
# built while paging/inspection are being layered over the working DTX path.
list(FILTER MEMO_SOURCES EXCLUDE REGEX ".*/x64_memo_store\\.cpp$")

add_library(memo STATIC ${MEMO_SOURCES})

target_include_directories(memo
  PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

target_compile_definitions(memo
  PUBLIC DOTTALK_WITH_INDEX=$<BOOL:${DOTTALK_WITH_INDEX}>
)

target_link_libraries(memo PUBLIC xbase)

if (DOTTALK_WITH_INDEX AND TARGET xindex)
  target_link_libraries(memo PUBLIC xindex)
endif()

if (MSVC)
  target_compile_options(memo PRIVATE /W4 /permissive- /MP)
else()
  target_compile_options(memo PRIVATE -Wall -Wextra -Wpedantic)
endif()
