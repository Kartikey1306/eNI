# Runs the eni CLI and checks its exit status and combined stdout/stderr.
#
#   -DENI_CLI=<path>          CLI binary
#   -DCLI_ARGS="<args>"       space-separated arguments
#   -DEXPECT_EXIT=zero|nonzero
#   -DREQUIRE=<regex>         must match (optional)
#   -DFORBID=<regex>          must not match (optional)
#   -DPOSITIVE=<regex>        first capture group must be an integer > 0 (optional)

if(NOT ENI_CLI OR NOT EXPECT_EXIT)
    message(FATAL_ERROR "cli_check.cmake: ENI_CLI and EXPECT_EXIT are required")
endif()

separate_arguments(args UNIX_COMMAND "${CLI_ARGS}")
execute_process(
    COMMAND "${ENI_CLI}" ${args}
    RESULT_VARIABLE rc
    OUTPUT_VARIABLE out
    ERROR_VARIABLE  out
    TIMEOUT 60
)
message("$ ${ENI_CLI} ${CLI_ARGS}  (exit=${rc})\n${out}")

set(errors "")
if(EXPECT_EXIT STREQUAL "zero")
    if(NOT rc STREQUAL "0")
        string(APPEND errors "expected exit 0, got '${rc}'\n")
    endif()
elseif(EXPECT_EXIT STREQUAL "nonzero")
    if(rc STREQUAL "0" OR NOT rc MATCHES "^[0-9]+$")
        string(APPEND errors "expected a nonzero exit code, got '${rc}'\n")
    endif()
else()
    message(FATAL_ERROR "cli_check.cmake: EXPECT_EXIT must be zero or nonzero")
endif()

if(DEFINED REQUIRE AND NOT out MATCHES "${REQUIRE}")
    string(APPEND errors "required output not found: ${REQUIRE}\n")
endif()
if(DEFINED FORBID AND out MATCHES "${FORBID}")
    string(APPEND errors "forbidden output found: '${CMAKE_MATCH_0}' (pattern ${FORBID})\n")
endif()
if(DEFINED POSITIVE)
    if(out MATCHES "${POSITIVE}")
        if(NOT CMAKE_MATCH_1 GREATER 0)
            string(APPEND errors "'${CMAKE_MATCH_0}' is not > 0\n")
        endif()
    else()
        string(APPEND errors "counter not found: ${POSITIVE}\n")
    endif()
endif()

if(errors)
    message(FATAL_ERROR "CLI check failed:\n${errors}")
endif()
