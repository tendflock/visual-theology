using System;
using System.Runtime.InteropServices;
using System.Text;

namespace FormatTest2;

class Program
{
    const string SinaiInterop = "/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/Resources/lib/libSinaiInterop.dylib";

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void ManagedDebuggerBreakDelegate();

    [DllImport(SinaiInterop)] static extern void LogosLibraryInitializationWrapper_Initialize(ManagedDebuggerBreakDelegate pfn);
    [DllImport(SinaiInterop)] static extern void LogosLibraryInitializationWrapper_Uninitialize();

    [DllImport(SinaiInterop)]
    static extern IntPtr LicenseManagerCore_New([MarshalAs(UnmanagedType.LPWStr)] string userId, [MarshalAs(UnmanagedType.LPWStr)] string path);
    [DllImport(SinaiInterop)] static extern void LicenseManagerCore_LoadCore(IntPtr ptr);
    [DllImport(SinaiInterop)] static extern void LicenseManagerCore_Delete(IntPtr ptr);

    // EncryptedVolume
    [DllImport(SinaiInterop)] static extern IntPtr EncryptedVolume_New();
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool EncryptedVolume_Open(IntPtr vol, IntPtr licMgr, [MarshalAs(UnmanagedType.LPWStr)] string path);
    [DllImport(SinaiInterop)] static extern IntPtr EncryptedVolume_OpenFile(IntPtr vol, [MarshalAs(UnmanagedType.LPWStr)] string name);
    [DllImport(SinaiInterop)] static extern IntPtr EncryptedVolume_OpenDatabase(IntPtr vol, [MarshalAs(UnmanagedType.LPWStr)] string name);
    [DllImport(SinaiInterop)] static extern IntPtr EncryptedVolume_CreateConnectionStringDataSource(IntPtr vol, [MarshalAs(UnmanagedType.LPWStr)] string name);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetResourceId(IntPtr vol);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetResourceDriverName(IntPtr vol);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetResourceDriverVersion(IntPtr vol);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetResourceVersion(IntPtr vol);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetDataTypesRequiredVersion(IntPtr vol);
    [DllImport(SinaiInterop)] static extern void EncryptedVolume_Delete(IntPtr vol);

    // EfsVolumeProxy
    [DllImport(SinaiInterop)] static extern IntPtr EfsVolumeProxy_New();
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool EfsVolumeProxy_TryOpenFromFile(IntPtr efs, IntPtr licMgr, [MarshalAs(UnmanagedType.LPWStr)] string path, [MarshalAs(UnmanagedType.LPWStr)] string? resourceId);
    [DllImport(SinaiInterop)]
    static extern IntPtr EfsVolumeProxy_TryOpenStream(IntPtr efs, [MarshalAs(UnmanagedType.LPWStr)] string streamName);
    [DllImport(SinaiInterop)] static extern void EfsVolumeProxy_Delete(IntPtr efs);

    // ReverseInterlinearData
    [DllImport(SinaiInterop)]
    static extern IntPtr ReverseInterlinearData_New(IntPtr licMgr, [MarshalAs(UnmanagedType.LPWStr)] string path);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string ReverseInterlinearData_ResourceIdToVersion(IntPtr rvi, [MarshalAs(UnmanagedType.LPWStr)] string resId);
    [DllImport(SinaiInterop)] static extern void ReverseInterlinearData_Delete(IntPtr rvi);

    static ManagedDebuggerBreakDelegate s_debugBreak = () => Console.Error.WriteLine("[Native assertion]");

    static void Main(string[] args)
    {
        string userId = "5621617";
        string licenseFolder = "/Volumes/External/Logos4/Data/e3txalek.5iq/LicenseManager";
        string resourcesBase = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources";

        try
        {
            Console.WriteLine("[INIT] Starting...");
            LogosLibraryInitializationWrapper_Initialize(s_debugBreak);
            IntPtr licMgr = LicenseManagerCore_New(userId, licenseFolder);
            LicenseManagerCore_LoadCore(licMgr);
            Console.WriteLine("[INIT] Ready.\n");

            // ============== TEST 1: EncryptedVolume OpenFile/OpenDatabase ==============
            string[] testFiles = { "BIBLEXREFS.lbslcr", "Lemmas.lbslms", "ESVNT.lbsrvi" };
            foreach (string file in testFiles)
            {
                string fullPath = $"{resourcesBase}/{file}";
                Console.WriteLine($"{'=',-60}");
                Console.WriteLine($"TEST: EncryptedVolume on {file}");
                Console.WriteLine($"{'=',-60}");

                IntPtr vol = EncryptedVolume_New();
                if (!EncryptedVolume_Open(vol, licMgr, fullPath))
                {
                    Console.WriteLine("  Open FAILED");
                    EncryptedVolume_Delete(vol);
                    continue;
                }

                Console.WriteLine($"  ResourceId: {EncryptedVolume_GetResourceId(vol)}");
                Console.WriteLine($"  Driver: {EncryptedVolume_GetResourceDriverName(vol)}");
                Console.WriteLine($"  DriverVersion: {EncryptedVolume_GetResourceDriverVersion(vol)}");
                Console.WriteLine($"  Version: {EncryptedVolume_GetResourceVersion(vol)}");

                string[] fileNames = { "", "data", "content", "index", "main", "metadata",
                    "crossreferences", "xrefs", "lemmas", "interlinear", "reverseinterlinear",
                    "0", "1", "data.db" };

                Console.WriteLine("\n  OpenFile results:");
                foreach (string name in fileNames)
                {
                    try
                    {
                        IntPtr stream = EncryptedVolume_OpenFile(vol, name);
                        Console.WriteLine($"    \"{name}\": {(stream != IntPtr.Zero ? $"ptr={stream}" : "null")}");
                    }
                    catch (Exception ex) { Console.WriteLine($"    \"{name}\": EXCEPTION {ex.Message}"); }
                }

                Console.WriteLine("\n  OpenDatabase results:");
                foreach (string name in fileNames)
                {
                    try
                    {
                        IntPtr db = EncryptedVolume_OpenDatabase(vol, name);
                        Console.WriteLine($"    \"{name}\": {(db != IntPtr.Zero ? $"ptr={db}" : "null")}");
                    }
                    catch (Exception ex) { Console.WriteLine($"    \"{name}\": EXCEPTION {ex.Message}"); }
                }

                EncryptedVolume_Delete(vol);
                Console.WriteLine();
            }

            // ============== TEST 2: EfsVolumeProxy ==============
            foreach (string file in testFiles)
            {
                string fullPath = $"{resourcesBase}/{file}";
                Console.WriteLine($"{'=',-60}");
                Console.WriteLine($"TEST: EfsVolumeProxy on {file}");
                Console.WriteLine($"{'=',-60}");

                IntPtr efs = EfsVolumeProxy_New();
                if (efs == IntPtr.Zero)
                {
                    Console.WriteLine("  New() returned null");
                    continue;
                }

                bool opened = false;
                try
                {
                    opened = EfsVolumeProxy_TryOpenFromFile(efs, licMgr, fullPath, null);
                    Console.WriteLine($"  TryOpenFromFile(null): {opened}");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  TryOpenFromFile(null): EXCEPTION {ex.Message}");
                }

                if (opened)
                {
                    string[] streamNames = { "", "data", "content", "index", "main",
                        "crossreferences", "xrefs", "lemmas", "interlinear", "0", "1" };
                    foreach (string sn in streamNames)
                    {
                        try
                        {
                            IntPtr stream = EfsVolumeProxy_TryOpenStream(efs, sn);
                            Console.WriteLine($"    Stream(\"{sn}\"): {(stream != IntPtr.Zero ? $"ptr={stream}" : "null")}");
                        }
                        catch (Exception ex) { Console.WriteLine($"    Stream(\"{sn}\"): EXCEPTION {ex.Message}"); }
                    }
                }

                EfsVolumeProxy_Delete(efs);
                Console.WriteLine();
            }

            // ============== TEST 3: ReverseInterlinearData with real resource IDs ==============
            Console.WriteLine($"{'=',-60}");
            Console.WriteLine("TEST: ReverseInterlinearData on ESVNT.lbsrvi");
            Console.WriteLine($"{'=',-60}");
            try
            {
                string rviPath = $"{resourcesBase}/ESVNT.lbsrvi";
                IntPtr rvi = ReverseInterlinearData_New(licMgr, rviPath);
                Console.WriteLine($"  Created: {rvi != IntPtr.Zero}");
                if (rvi != IntPtr.Zero)
                {
                    // Try resource IDs from actual .logos4 files we know exist
                    string[] rids = {
                        "ESVNT", "RVI:ESVNT",
                        "LLS:ESV", "LLS:1.0.6",
                        "LLS:SBLGNT", "LLS:NA28",
                        "LLS:1.0.710", "LLS:1.0.30",
                        // Bible abbreviation formats
                        "bible.esv", "bible.63.esv",
                        "ESV", "ESV-NT",
                    };
                    foreach (string rid in rids)
                    {
                        try
                        {
                            string ver = ReverseInterlinearData_ResourceIdToVersion(rvi, rid);
                            Console.WriteLine($"    \"{rid}\": \"{ver ?? "(null)"}\"");
                        }
                        catch (Exception ex) { Console.WriteLine($"    \"{rid}\": EXCEPTION {ex.Message}"); }
                    }
                    ReverseInterlinearData_Delete(rvi);
                }
            }
            catch (Exception ex) { Console.WriteLine($"  EXCEPTION: {ex.Message}"); }

            // ============== TEST 4: ReverseInterlinearData on NASBNT ==============
            Console.WriteLine($"\n{'=',-60}");
            Console.WriteLine("TEST: ReverseInterlinearData on NASBNT.lbsrvi");
            Console.WriteLine($"{'=',-60}");
            try
            {
                string rviPath = $"{resourcesBase}/NASBNT.lbsrvi";
                IntPtr rvi = ReverseInterlinearData_New(licMgr, rviPath);
                Console.WriteLine($"  Created: {rvi != IntPtr.Zero}");
                if (rvi != IntPtr.Zero)
                {
                    string[] rids = { "NASBNT", "RVI:NASBNT", "LLS:NASB", "LLS:1.0.7", "NASB", "LLS:NASB95" };
                    foreach (string rid in rids)
                    {
                        try
                        {
                            string ver = ReverseInterlinearData_ResourceIdToVersion(rvi, rid);
                            Console.WriteLine($"    \"{rid}\": \"{ver ?? "(null)"}\"");
                        }
                        catch (Exception ex) { Console.WriteLine($"    \"{rid}\": EXCEPTION {ex.Message}"); }
                    }
                    ReverseInterlinearData_Delete(rvi);
                }
            }
            catch (Exception ex) { Console.WriteLine($"  EXCEPTION: {ex.Message}"); }

            Console.WriteLine("\n[DONE]");
            LogosLibraryInitializationWrapper_Uninitialize();
            LicenseManagerCore_Delete(licMgr);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[FATAL] {ex.GetType().Name}: {ex.Message}");
            Console.WriteLine(ex.StackTrace);
        }
    }
}
