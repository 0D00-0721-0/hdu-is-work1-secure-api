# Fixed Tomcat release. The official image does not enable the AJP connector.
FROM tomcat:9.0.31

# Restore the default web applications so the HTTP homepage can be checked.
RUN cp -r $CATALINA_HOME/webapps.dist/* $CATALINA_HOME/webapps/
