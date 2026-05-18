// Export Ghidra Decompiler pseudocode for IL2CPP user-code methods to .c files.
// Filters to Assembly-CSharp / Assembly-CSharp-firstpass / __Generated namespaces only,
// skipping mscorlib / System / Unity / SevenZip / Newtonsoft etc. (which we don't need to AI-restore).
//@category IL2CPP
//@runtime Java

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;

public class ExportPseudocode extends GhidraScript {

    private static final String OUT_DIR = "/Users/wellstseng/project/Il2CppDumper/Input/output/pseudocode/";
    private static final String TARGET_RVAS = "/Users/wellstseng/project/Il2CppDumper/Input/output/_target_rvas.tsv";

    @Override
    protected void run() throws Exception {
        Files.createDirectories(Paths.get(OUT_DIR));

        // Load target RVAs (offset relative to image base) prepared by preprocess
        Set<Long> targetOffsets = new HashSet<>();
        try (BufferedReader r = new BufferedReader(new FileReader(TARGET_RVAS))) {
            String line;
            while ((line = r.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                try { targetOffsets.add(Long.parseLong(line)); } catch (NumberFormatException ignore) {}
            }
        }
        println("ExportPseudocode: target methods = " + targetOffsets.size());

        DecompInterface decomp = new DecompInterface();
        decomp.setOptions(new DecompileOptions());
        if (!decomp.openProgram(currentProgram)) {
            println("ExportPseudocode: failed to open program with decompiler");
            return;
        }

        Address base = currentProgram.getImageBase();
        FunctionIterator funcs = currentProgram.getFunctionManager().getFunctions(true);
        ConsoleTaskMonitor monitor = new ConsoleTaskMonitor();

        int processed = 0, written = 0, skipped = 0, failed = 0;
        long t0 = System.currentTimeMillis();

        for (Function f : funcs) {
            long off = f.getEntryPoint().subtract(base);
            if (!targetOffsets.contains(off)) { skipped++; continue; }
            processed++;

            DecompileResults res = decomp.decompileFunction(f, 60, monitor);
            if (res == null || !res.decompileCompleted()) {
                failed++;
                if (failed <= 5) println("decompile failed: " + f.getName() + " @ " + f.getEntryPoint());
                continue;
            }
            String code = res.getDecompiledFunction().getC();
            if (code == null || code.isEmpty()) { failed++; continue; }

            // Filename: <RVA_hex>__<sanitized name>.c
            String name = f.getName().replaceAll("[^A-Za-z0-9_\\-\\.]", "_");
            if (name.length() > 180) name = name.substring(0, 180);
            String fname = String.format("%08x__%s.c", off, name);
            Path out = Paths.get(OUT_DIR, fname);

            try (PrintWriter pw = new PrintWriter(Files.newBufferedWriter(out))) {
                pw.println("// RVA: 0x" + Long.toHexString(off));
                pw.println("// Function: " + f.getName());
                pw.println("// EntryPoint: " + f.getEntryPoint());
                pw.println();
                pw.print(code);
            }
            written++;

            if (written % 200 == 0) {
                long el = (System.currentTimeMillis() - t0) / 1000;
                println(String.format("progress: %d written, %ds elapsed", written, el));
            }
        }
        decomp.closeProgram();

        long el = (System.currentTimeMillis() - t0) / 1000;
        println(String.format("ExportPseudocode: DONE processed=%d written=%d skipped=%d failed=%d elapsed=%ds",
                processed, written, skipped, failed, el));
    }
}
