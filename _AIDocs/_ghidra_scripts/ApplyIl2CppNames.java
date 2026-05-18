// Apply IL2CPP names from preprocessed TSV files (avoids PyGhidra SIGBUS on macOS Tahoe ARM64)
//@category IL2CPP
//@runtime Java

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.SourceType;
import java.io.BufferedReader;
import java.io.FileReader;

public class ApplyIl2CppNames extends GhidraScript {

    private static final String BASE = "/Users/wellstseng/project/Il2CppDumper/Input/output/";

    @Override
    protected void run() throws Exception {
        Address baseAddr = currentProgram.getImageBase();

        int methods = applyLabels(baseAddr, BASE + "_methods.tsv", null, false);
        println("ApplyIl2CppNames: methods labelled = " + methods);

        int strings = applyLabels(baseAddr, BASE + "_strings.tsv", "StringLiteral_", true);
        println("ApplyIl2CppNames: strings labelled = " + strings);

        int meta = applyLabels(baseAddr, BASE + "_metadata.tsv", null, true);
        println("ApplyIl2CppNames: metadata labelled = " + meta);

        int mmethods = applyLabels(baseAddr, BASE + "_metadata_methods.tsv", null, true);
        println("ApplyIl2CppNames: metadata-methods labelled = " + mmethods);

        int funcs = createFunctions(baseAddr, BASE + "_addresses.tsv");
        println("ApplyIl2CppNames: functions created = " + funcs);

        println("ApplyIl2CppNames: DONE");
    }

    private int applyLabels(Address base, String path, String namePrefix, boolean addEolComment) throws Exception {
        int ok = 0;
        int idx = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = r.readLine()) != null) {
                idx++;
                int tab = line.indexOf('\t');
                if (tab < 0) continue;
                long offset;
                try { offset = Long.parseLong(line.substring(0, tab)); }
                catch (NumberFormatException e) { continue; }
                String name = line.substring(tab + 1);
                String label = (namePrefix != null) ? namePrefix + idx : name.replace(' ', '-');
                try {
                    Address a = base.add(offset);
                    createLabel(a, label, true, SourceType.USER_DEFINED);
                    if (addEolComment) setEOLComment(a, name);
                    ok++;
                } catch (Exception e) {
                    // skip out-of-range / invalid addresses
                }
            }
        }
        return ok;
    }

    private int createFunctions(Address base, String path) throws Exception {
        int ok = 0;
        try (BufferedReader r = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = r.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                long offset;
                try { offset = Long.parseLong(line); }
                catch (NumberFormatException e) { continue; }
                try {
                    Address a = base.add(offset);
                    if (getFunctionAt(a) == null) {
                        createFunction(a, null);
                    }
                    ok++;
                } catch (Exception e) {
                    // skip
                }
            }
        }
        return ok;
    }
}
