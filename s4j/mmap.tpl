package {{ns}}

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;
import java.util.concurrent.atomic.AtomicInteger;

// Auto generated. do not edit
public class {{cls}} {

    final String file;
    private final AtomicInteger mIdx = new AtomicInteger(-1);

    final MappedByteBuffer mBuffer;

    public {{cls}}(String file) throws IOException {
        this.file = file;

        FileChannel ch = new RandomAccessFile(new File(file), "rw").getChannel();
        // 2G file
        this.mBuffer = ch.map(FileChannel.MapMode.READ_WRITE, 0, Integer.MAX_VALUE);
    }

    public int append(Property p) {
        int idx = this.mIdx.incrementAndGet();

        {% for f in fields %}
        this.mBuffer.put{{f.Java}}(idx * {{sizeof}} + {{f.off}}, p.{{f.name}});{% end %}

        this.mBuffer.putInt(0, size());
        return idx;
    }

    public int size() {
        return this.mIdx.get();
    }

    public String getFile() {
        return this.file;
    }

    {% for f in fields %}
    public {{f.java}} get{{f.Name}}(int idx) {
        return this.mBuffer.get{{f.Java}}(idx * {{sizeof}} + {{f.off}});
    }{% end %}

    public static class Property {
    {% for f in fields %}
        public {{f.java}} {{f.name}};{% end %}
    }
}
