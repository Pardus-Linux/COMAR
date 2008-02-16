PROJECT (comar-dbus)

# Application name
SET (APP_NAME "comar")
SET (APP_SUFFIX "")

# Version string
SET (VERSION_MAJOR "2")
SET (VERSION_MINOR "0")
SET (VERSION_PATCH "0")

# Uncomment this for production releases.
SET (VERSION_SUFFIX "alpha1")
SET (FLAGS "-g -O0 -Werror -Wcast-align -Wno-uninitialized -Wall -fstrict-aliasing") # -fprofile-arcs -ftest-coverage")
SET (CMAKE_C_FLAGS "${FLAGS}")

# Append version suffix, if specified
SET (VERSION ${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH})
IF (VERSION_SUFFIX)
   SET (VERSION "${VERSION}_${VERSION_SUFFIX}")
ENDIF (VERSION_SUFFIX)

# Append name suffix, if specified
IF (APP_SUFFIX)
   SET (APP_NAME "${APP_NAME}${APP_SUFFIX}")
ENDIF (APP_SUFFIX)

# Define version, config dir, data dir and log file.
ADD_DEFINITIONS (-D'VERSION="${VERSION}"'
                 -D'CONFIG_DIR="/etc/${APP_NAME}"'
                 -D'DATA_DIR="/var/db/${APP_NAME}"'
                 -D'PID_FILE="/var/run/${APP_NAME}.pid"'
                 -D'LOG_FILE="/var/log/${APP_NAME}.log"')

# Set standard sources
SET (SOURCES src/main.c
             src/cfg.c
             src/csl.c
             src/data.c
             src/dbus.c
             src/iksemel.c
             src/log.c
             src/process.c
             src/pydbus.c
             src/policy.c
             src/model.c
             src/utility.c)

# Set standard libraries
SET (LIBS python2.4
          dbus-1
          polkit-dbus
          db)

# Include standard headers
INCLUDE_DIRECTORIES (include/
                     /usr/include/python2.4
                     /usr/include/dbus-1.0
                     /usr/lib/dbus-1.0/include
                     /usr/include/PolicyKit)

# Load CMAKE modules
SET (CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake_modules/")

# Check if system has PolicyKit
# PK is not a required dependency in SVN builds.
FIND_PACKAGE (PolicyKit REQUIRED)

# Compile comar from specified sources
ADD_EXECUTABLE (comar ${SOURCES})

# Link comar to specified libraries
TARGET_LINK_LIBRARIES(comar ${LIBS} )

# Install comar to /usr/bin/<app-name>
INSTALL (PROGRAMS comar
         DESTINATION /usr/bin
         RENAME ${APP_NAME})

# Install comar cli to /usr/bin/hav${APP_SUFFIX}
INSTALL (PROGRAMS tools/hav.py
         DESTINATION /usr/bin
         RENAME hav${APP_SUFFIX})

# Install model file under /etc/<app-name>/
INSTALL (FILES etc/model.xml
         DESTINATION /etc/${APP_NAME})

# Install comar system bus configuration under /etc/dbus-1/system.d/
INSTALL (FILES
         etc/comar.conf
         DESTINATION /etc/dbus-1/system.d
         RENAME ${APP_NAME}.conf)

# Install comar service activation under /usr/share/dbus-1/system-services/
INSTALL (FILES
         etc/tr.org.pardus.comar.service
         etc/tr.org.pardus.comar.new.service
         DESTINATION /usr/share/dbus-1/system-services/)

# Install PK policies
INSTALL (DIRECTORY
        etc/policy
        DESTINATION /usr/share/PolicyKit
        PATTERN ".svn" EXCLUDE)
