using System;
using System.Runtime.InteropServices;

namespace FormatTest3;

/// <summary>
/// Test 3: Control test (what works with .logos4?) and focused RVI/Lemma testing.
/// Also try EfsVolumeProxy more carefully.
/// </summary>
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
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetResourceId(IntPtr vol);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)] static extern string EncryptedVolume_GetResourceDriverName(IntPtr vol);
    [DllImport(SinaiInterop)] static extern void EncryptedVolume_Delete(IntPtr vol);

    // CTitle for loaded resources
    enum TitleLoadHint : int { Normal = 0 }
    enum TitleLoadResult : int { Failed = 0, Locked = 1, VersionIncompatible = 2, Success = 3 }
    [DllImport(SinaiInterop)]
    static extern IntPtr SinaiInterop_LoadTitleWithoutDataTypeOptions(
        IntPtr licMgr, IntPtr dtm, [MarshalAs(UnmanagedType.LPWStr)] string path,
        IntPtr stream, [MarshalAs(UnmanagedType.LPWStr)] string? driverVer,
        [MarshalAs(UnmanagedType.LPWStr)] string? dtVer, TitleLoadHint hint, out TitleLoadResult result);

    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_IsArticle(IntPtr title, int article);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_ArticleNumberToArticleId(IntPtr title, int article, [MarshalAs(UnmanagedType.LPWStr)] out string artId);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceId(IntPtr title);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_HasReverseInterlinear(IntPtr title);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_HasInterlinear(IntPtr title);
    [DllImport(SinaiInterop)]
    static extern IntPtr CTitle_GetReverseInterlinearData(IntPtr title);
    [DllImport(SinaiInterop)]
    static extern IntPtr CTitle_GetInterlinearData(IntPtr title);
    [DllImport(SinaiInterop)]
    static extern IntPtr CTitle_GetLemmaReferenceFinder(IntPtr title);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_IsBible(IntPtr title);

    // ResourceVolume
    [DllImport(SinaiInterop)]
    static extern IntPtr SinaiInterop_ResourceVolumeFromResource(IntPtr resource);

    // ReverseInterlinearData
    [DllImport(SinaiInterop)]
    static extern IntPtr ReverseInterlinearData_New(IntPtr licMgr, [MarshalAs(UnmanagedType.LPWStr)] string path);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string ReverseInterlinearData_ResourceIdToVersion(IntPtr rvi, [MarshalAs(UnmanagedType.LPWStr)] string resId);
    [DllImport(SinaiInterop)] static extern void ReverseInterlinearData_Delete(IntPtr rvi);

    // SinaiInterop_GetSupportedDriverVersions
    [DllImport(SinaiInterop)]
    static extern IntPtr SinaiInterop_GetSupportedDriverVersions([MarshalAs(UnmanagedType.LPWStr)] string driverName);

    static ManagedDebuggerBreakDelegate s_debugBreak = () => Console.Error.WriteLine("[Native assertion]");

    static void Main(string[] args)
    {
        string userId = "5621617";
        string licenseFolder = "/Volumes/External/Logos4/Data/e3txalek.5iq/LicenseManager";
        string resourcesBase = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources";

        try
        {
            LogosLibraryInitializationWrapper_Initialize(s_debugBreak);
            IntPtr licMgr = LicenseManagerCore_New(userId, licenseFolder);
            LicenseManagerCore_LoadCore(licMgr);
            Console.WriteLine("[INIT] Ready.\n");

            // TEST A: Control - Open a .logos4 file and check its capabilities
            Console.WriteLine("=== TEST A: Control - ESV.logos4 capabilities ===");
            {
                string esvPath = $"{resourcesBase}/ESV.logos4";
                if (System.IO.File.Exists(esvPath))
                {
                    IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                        licMgr, IntPtr.Zero, esvPath, IntPtr.Zero, null, null,
                        TitleLoadHint.Normal, out TitleLoadResult result);
                    Console.WriteLine($"  ESV.logos4 load: {result}");
                    if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                    {
                        string rid = SinaiInterop_CTitle_GetResourceId(title);
                        Console.WriteLine($"  ResourceId: {rid}");

                        try { Console.WriteLine($"  IsBible: {CTitle_IsBible(title)}"); } catch (Exception ex) { Console.WriteLine($"  IsBible: EXCEPTION {ex.Message}"); }
                        try { Console.WriteLine($"  HasReverseInterlinear: {CTitle_HasReverseInterlinear(title)}"); } catch (Exception ex) { Console.WriteLine($"  HasReverseInterlinear: EXCEPTION {ex.Message}"); }
                        try { Console.WriteLine($"  HasInterlinear: {CTitle_HasInterlinear(title)}"); } catch (Exception ex) { Console.WriteLine($"  HasInterlinear: EXCEPTION {ex.Message}"); }
                        try
                        {
                            IntPtr rviData = CTitle_GetReverseInterlinearData(title);
                            Console.WriteLine($"  GetReverseInterlinearData: {(rviData != IntPtr.Zero ? $"ptr={rviData}" : "null")}");
                        }
                        catch (Exception ex) { Console.WriteLine($"  GetReverseInterlinearData: EXCEPTION {ex.Message}"); }
                        try
                        {
                            IntPtr intData = CTitle_GetInterlinearData(title);
                            Console.WriteLine($"  GetInterlinearData: {(intData != IntPtr.Zero ? $"ptr={intData}" : "null")}");
                        }
                        catch (Exception ex) { Console.WriteLine($"  GetInterlinearData: EXCEPTION {ex.Message}"); }
                        try
                        {
                            IntPtr lemmaFinder = CTitle_GetLemmaReferenceFinder(title);
                            Console.WriteLine($"  GetLemmaReferenceFinder: {(lemmaFinder != IntPtr.Zero ? $"ptr={lemmaFinder}" : "null")}");
                        }
                        catch (Exception ex) { Console.WriteLine($"  GetLemmaReferenceFinder: EXCEPTION {ex.Message}"); }

                        // Also try EncryptedVolume on a .logos4 file for comparison
                        Console.WriteLine("\n  EncryptedVolume control test on ESV.logos4:");
                        IntPtr vol = EncryptedVolume_New();
                        if (EncryptedVolume_Open(vol, licMgr, esvPath))
                        {
                            Console.WriteLine($"    Driver: {EncryptedVolume_GetResourceDriverName(vol)}");
                            string[] tryNames = { "", "data", "content", "index", "main", "0", "1" };
                            foreach (string n in tryNames)
                            {
                                IntPtr f = EncryptedVolume_OpenFile(vol, n);
                                IntPtr d = EncryptedVolume_OpenDatabase(vol, n);
                                if (f != IntPtr.Zero) Console.WriteLine($"    OpenFile(\"{n}\"): ptr={f}");
                                if (d != IntPtr.Zero) Console.WriteLine($"    OpenDatabase(\"{n}\"): ptr={d}");
                            }
                        }
                        else
                        {
                            Console.WriteLine("    Open FAILED");
                        }
                        EncryptedVolume_Delete(vol);
                    }
                }
                else
                {
                    Console.WriteLine("  ESV.logos4 not found, trying KJV1900.logos4...");
                    // Try other bibles
                    foreach (string tryFile in new[] { "KJV1900.logos4", "NASB95.logos4", "NIV2011.logos4" })
                    {
                        string tryPath = $"{resourcesBase}/{tryFile}";
                        if (System.IO.File.Exists(tryPath))
                        {
                            Console.WriteLine($"  Found: {tryFile}");
                            IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                                licMgr, IntPtr.Zero, tryPath, IntPtr.Zero, null, null,
                                TitleLoadHint.Normal, out TitleLoadResult result);
                            if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                            {
                                try { Console.WriteLine($"    HasReverseInterlinear: {CTitle_HasReverseInterlinear(title)}"); } catch { }
                                try { Console.WriteLine($"    HasInterlinear: {CTitle_HasInterlinear(title)}"); } catch { }
                                try
                                {
                                    IntPtr rviData = CTitle_GetReverseInterlinearData(title);
                                    Console.WriteLine($"    GetReverseInterlinearData: {(rviData != IntPtr.Zero ? $"ptr={rviData}" : "null")}");
                                }
                                catch { }
                            }
                            break;
                        }
                    }
                }
            }

            // TEST B: Check supported driver versions
            Console.WriteLine("\n=== TEST B: GetSupportedDriverVersions ===");
            foreach (string driverName in new[] { "BibleCrossReferences", "Lemmas", "ReverseInterlinear", "Logos4Book", "LDLSBook" })
            {
                try
                {
                    IntPtr versionsPtr = SinaiInterop_GetSupportedDriverVersions(driverName);
                    Console.WriteLine($"  {driverName}: ptr={versionsPtr}");
                    if (versionsPtr != IntPtr.Zero)
                    {
                        // Try to read as vector of strings
                        // First element is the count (int)
                        int count = Marshal.ReadInt32(versionsPtr);
                        Console.WriteLine($"    Count/FirstInt: {count}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  {driverName}: EXCEPTION {ex.Message}");
                }
            }

            // TEST C: ReverseInterlinearData with comprehensive resource IDs
            Console.WriteLine("\n=== TEST C: ReverseInterlinearData ===");
            {
                string rviPath = $"{resourcesBase}/ESVNT.lbsrvi";
                IntPtr rvi = ReverseInterlinearData_New(licMgr, rviPath);
                Console.WriteLine($"  Created for ESVNT.lbsrvi: {rvi != IntPtr.Zero}");
                if (rvi != IntPtr.Zero)
                {
                    // The resource ID format in Logos is typically "LLS:1.0.NUMBER"
                    // Let me try a range of IDs
                    Console.WriteLine("  Testing resource IDs:");

                    // Try some known resource IDs from the resources folder
                    string[] knownIds = {
                        // ESV-related
                        "ESVNT", "RVI:ESVNT", "LLS:ESV",
                        "LLS:1.0.6", "LLS:1.0.5", "LLS:1.0.7",
                        "LLS:ESV-STUDY", "bible.esv",
                        // SBLGNT/NA28 (Greek sources the ESV reverse interlinear would map to)
                        "LLS:SBLGNT", "LLS:NA28", "LLS:1.0.710", "LLS:1.0.30",
                        "LLS:1.0.15", "LLS:1.0.62",
                        // Other patterns
                        "", "ESV", "SBLGNT",
                    };
                    foreach (string rid in knownIds)
                    {
                        try
                        {
                            string ver = ReverseInterlinearData_ResourceIdToVersion(rvi, rid);
                            string display = ver == null ? "(null)" : (ver.Length == 0 ? "(empty)" : ver);
                            Console.WriteLine($"    \"{rid}\": {display}");
                        }
                        catch (Exception ex) { Console.WriteLine($"    \"{rid}\": EXCEPTION {ex.Message}"); }
                    }
                    ReverseInterlinearData_Delete(rvi);
                }
            }

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
