#pragma once

void print_key(char *input)
{
  char buf[1024];
  FILE *fp = fopen("flag", "r");
  if (!fp)
    err(1, "Failed to locate the flag file!");

  while (1) {
    size_t len = fread(buf, 1, sizeof(buf)-1, fp);
    buf[len] = '\0';
    printf("%s", buf);
    if (len < sizeof(buf)-1)
      break;
  }
  fclose(fp);
}
