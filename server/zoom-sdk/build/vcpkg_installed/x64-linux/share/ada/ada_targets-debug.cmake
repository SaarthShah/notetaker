#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debug".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "ada::ada" for configuration "Debug"
set_property(TARGET ada::ada APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBUG)
set_target_properties(ada::ada PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_DEBUG "CXX"
  IMPORTED_LOCATION_DEBUG "${_IMPORT_PREFIX}/debug/lib/libada.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS ada::ada )
list(APPEND _IMPORT_CHECK_FILES_FOR_ada::ada "${_IMPORT_PREFIX}/debug/lib/libada.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
