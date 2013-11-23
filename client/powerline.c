/* vim:fileencoding=utf-8:noet
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <errno.h>

#define handle_error(msg) \
	do { perror(msg); exit(EXIT_FAILURE); } while (0)

#ifndef TEMP_FAILURE_RETRY
#define TEMP_FAILURE_RETRY(expression) \
  (                                                                           \
	({ long int __result;                                                     \
	   do __result = (long int) (expression);                                 \
	   while (__result == -1L && errno == EINTR);                             \
	   __result; }))
#endif

extern char **environ;

void do_write(int sd, const char *raw, int len) {
	int written = 0, n = -1;

	while (written < len) {
		n = TEMP_FAILURE_RETRY(write(sd, raw+written, len-written));
		if (n == -1) {
			close(sd);
			handle_error("write() failed");
		}
		written += n;
	}
}

int main(int argc, char *argv[]) {
	int sd = -1, i;
	struct sockaddr_un server;
	char address[50] = {};
	const char eof[2] = "\0\0";
	char buf[4096] = {};
	char *newargv[200] = {};
	char *wd = NULL;
	char **envp;

	if (argc < 2) { printf("Must provide at least one argument.\n"); return EXIT_FAILURE; }

#ifdef __APPLE__
	snprintf(address, 50, "/tmp/powerline-ipc-%d", getuid());
#else
	snprintf(address, 50, "powerline-ipc-%d", getuid());
#endif

	sd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (sd == -1) handle_error("socket() failed");

	memset(&server, 0, sizeof(struct sockaddr_un)); // Clear 
	server.sun_family = AF_UNIX;
#ifdef __APPLE__
	strncpy(server.sun_path, address, strlen(address));
#else
	strncpy(server.sun_path+1, address, strlen(address));
#endif

#ifdef __APPLE__
	if (connect(sd, (struct sockaddr *) &server, sizeof(server.sun_family) + strlen(address)) < 0) {
#else
	if (connect(sd, (struct sockaddr *) &server, sizeof(server.sun_family) + strlen(address)+1) < 0) {
#endif
		close(sd);
		// We failed to connect to the daemon, execute powerline instead
		argc = (argc < 199) ? argc : 199;
		for (i=1; i < argc; i++) newargv[i] = argv[i];
		newargv[0] = "powerline-render";
		newargv[argc] = NULL;
		execvp("powerline-render", newargv);
	}

	for (i = 1; i < argc; i++) {
		do_write(sd, argv[i], strlen(argv[i]));
		do_write(sd, eof, 1);
	}

	for(envp=environ; *envp; envp++) {
		do_write(sd, "--env=", 6);
		do_write(sd, *envp, strlen(*envp));
		do_write(sd, eof, 1);
	}

	wd = getcwd(NULL, 0);
	if (wd != NULL) {
		do_write(sd, "--cwd=", 6);
		do_write(sd, wd, strlen(wd));
		free(wd); wd = NULL;
	}

	do_write(sd, eof, 2);

	i = -1;
	while (i != 0) {
		i = TEMP_FAILURE_RETRY(read(sd, buf, 4096));
		if (i == -1) {
			close(sd);
			handle_error("read() failed");
		}
		if (i > 0) 
			write(STDOUT_FILENO, buf, i) || 0;
	}

	close(sd);

	return 0;
}
