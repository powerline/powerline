/* vim:fileencoding=utf-8:noet
 */

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <sys/un.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

#define HANDLE_ERROR(msg) \
	do { \
		perror(msg); exit(EXIT_FAILURE); \
	} while (0)

#define TEMP_FAILURE_RETRY(var, expression) \
	do { \
		long int __result; \
		do { \
			__result = (long int) (expression); \
		} while (__result == -1L && errno == EINTR); \
		var = __result; \
	} while (0)

extern char **environ;

void do_write(int sd, const char *raw, size_t len) {
	size_t written = 0;
	ptrdiff_t n = -1;

	while (written < len) {
		TEMP_FAILURE_RETRY(n, write(sd, raw + written, len - written));
		if (n == -1) {
			close(sd);
			HANDLE_ERROR("write() failed");
		}
		written += (size_t) n;
	}
}

#ifdef __APPLE__
# define ADDRESS_TEMPLATE "/tmp/powerline-ipc-%d"
# define A
#else
# define ADDRESS_TEMPLATE "powerline-ipc-%d"
# define A +1
#endif

#define ADDRESS_SIZE sizeof(ADDRESS_TEMPLATE) + (sizeof(uid_t) * 4)
#define NUM_ARGS_SIZE (sizeof(int) * 2)
#define BUF_SIZE 4096
#define NEW_ARGV_SIZE 200

int main(int argc, char *argv[]) {
	int sd = -1;
	ptrdiff_t i;
	struct sockaddr_un server;
	char address[ADDRESS_SIZE];
	const char eof[2] = "\0\0";
	char num_args[NUM_ARGS_SIZE];
	char buf[BUF_SIZE];
	char *newargv[NEW_ARGV_SIZE];
	char *wd = NULL;
	char **envp;

	if (argc < 2) {
		printf("Must provide at least one argument.\n"); return EXIT_FAILURE;
	}

	snprintf(address, ADDRESS_SIZE, ADDRESS_TEMPLATE, getuid());

	sd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (sd == -1)
		HANDLE_ERROR("socket() failed");

	memset(&server, 0, sizeof(struct sockaddr_un));
	server.sun_family = AF_UNIX;
	strncpy(server.sun_path A, address, strlen(address));

	if (connect(sd, (struct sockaddr *) &server, (socklen_t) (sizeof(server.sun_family) + strlen(address) A)) < 0) {
		close(sd);
		/* We failed to connect to the daemon, execute powerline instead */
		argc = (argc < NEW_ARGV_SIZE - 1) ? argc : NEW_ARGV_SIZE - 1;
		for (i = 1; i < argc; i++)
			newargv[i] = argv[i];
		newargv[0] = "powerline-render";
		newargv[argc] = NULL;
		execvp("powerline-render", newargv);
	}

	snprintf(num_args, NUM_ARGS_SIZE, "%x", argc - 1);
	do_write(sd, num_args, strlen(num_args));
	do_write(sd, eof, 1);

	for (i = 1; i < argc; i++) {
		do_write(sd, argv[i], strlen(argv[i]));
		do_write(sd, eof, 1);
	}

	wd = getcwd(NULL, 0);
	if (wd != NULL) {
		do_write(sd, wd, strlen(wd));
		free(wd); wd = NULL;
	}

	for(envp=environ; *envp; envp++) {
		do_write(sd, *envp, strlen(*envp));
		do_write(sd, eof, 1);
	}

	do_write(sd, eof, 2);

	i = -1;
	while (i != 0) {
		TEMP_FAILURE_RETRY(i, read(sd, buf, BUF_SIZE));
		if (i == -1) {
			close(sd);
			HANDLE_ERROR("read() failed");
		} else if (i > 0) {
			(void) write(STDOUT_FILENO, buf, (size_t) i);
		}
	}

	close(sd);

	return 0;
}
