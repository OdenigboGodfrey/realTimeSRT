class SRTWriter:
    def __init__(self, path):
        self.f = open(path, "w", encoding="utf-8")
        self.idx = 1

    def _fmt(self, t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h:02}:{m:02}:{s:06.3f}".replace('.', ',')

    def write(self, start, end, text):
        self.f.write(f"{self.idx}\n")
        self.f.write(f"{self._fmt(start)} --> {self._fmt(end)}\n")
        self.f.write(text + "\n\n")
        self.idx += 1

    def close(self):
        self.f.close()