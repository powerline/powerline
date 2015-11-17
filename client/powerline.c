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
		perror(msg); \
		exit(EXIT_FAILURE); \
	} while (0)

#define TEMP_FAILURE_RETRY(var, expression) \
	do { \
		ptrdiff_t __result; \
		do { \
			__result = (expression); \
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

inline size_t true_sun_len(const struct sockaddr_un *ptr) {
#ifdef __linux__
	/* Because SUN_LEN uses strlen and abstract namespace paths begin
	 * with a null byte, SUN_LEN is broken for these. Passing the full
	 * struct size also fails on Linux, so compute manually. The
	 * abstract namespace is Linux-only. */
	if (ptr->sun_path[0] == '\0') {
		return sizeof(ptr->sun_family) + strlen(ptr->sun_path + 1) + 1;
	}
#endif
#ifdef SUN_LEN
	/* If the vendor provided SUN_LEN, we may as well use it. */
	return SUN_LEN(ptr);
#else
	/* SUN_LEN is not POSIX, so if it was not provided, use the struct
	 * size as a fallback. */
	return sizeof(struct sockaddr_un);
#endif
}

#ifdef __linux__
# define ADDRESS_TEMPLATE "powerline-ipc-%d"
# define A +1
#else
# define ADDRESS_TEMPLATE "/tmp/powerline-ipc-%d"
# define A
#endif

#define ADDRESS_SIZE sizeof(ADDRESS_TEMPLATE) + (sizeof(uid_t) * 4)
#define NUM_ARGS_SIZE (sizeof(int) * 2)
#define BUF_SIZE 4096
#define NEW_ARGV_SIZE 200

int main(int argc, char *argv[]) {
	int sd = -1;
	int i;
	ptrdiff_t read_size;
	struct sockaddr_un server;
	char address_buf[ADDRESS_SIZE];
	const char eof[2] = "\0\0";
	char num_args[NUM_ARGS_SIZE];
	char buf[BUF_SIZE];
	char *newargv[NEW_ARGV_SIZE];
	char *wd = NULL;
	char **envp;
	const char *address;

	if (argc < 2) {
		printf("Must provide at least one argument.\n");
		return EXIT_FAILURE;
	}

	if (argc > 3 && strcmp(argv[1], "--socket") == 0) {
		address = argv[2];
		argv += 2;
		argc -= 2;
	} else {
		snprintf(address_buf, ADDRESS_SIZE, ADDRESS_TEMPLATE, getuid());
		address = &(address_buf[0]);
	}

	sd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (sd == -1)
		HANDLE_ERROR("socket() failed");

	memset(&server, 0, sizeof(struct sockaddr_un));
	server.sun_family = AF_UNIX;
	strncpy(server.sun_path A, address, strlen(address));

	if (connect(sd, (struct sockaddr *) &server, true_sun_len(&server)) < 0) {
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
		free(wd);
		wd = NULL;
	}
	do_write(sd, eof, 1);

	for(envp=environ; *envp; envp++) {
		do_write(sd, *envp, strlen(*envp));
		do_write(sd, eof, 1);
	}

	do_write(sd, eof, 2);

	read_size = -1;
	while (read_size != 0) {
		TEMP_FAILURE_RETRY(read_size, read(sd, buf, BUF_SIZE));
		if (read_size == -1) {
			close(sd);
			HANDLE_ERROR("read() failed");
		} else if (read_size > 0) {
			do_write(STDOUT_FILENO, buf, (size_t) read_size);
		}
	}

	close(sd);

	return 0;
}
