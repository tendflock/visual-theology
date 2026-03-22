using System;
using System.Runtime.InteropServices;

namespace FormatTest4;

/// <summary>
/// Test 4: ReverseInterlinearData with known resource IDs,
/// and test what data the CTitle RVI/Interlinear accessors provide.
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

    enum TitleLoadHint : int { Normal = 0 }
    enum TitleLoadResult : int { Failed = 0, Locked = 1, VersionIncompatible = 2, Success = 3 }

    [DllImport(SinaiInterop)]
    static extern IntPtr SinaiInterop_LoadTitleWithoutDataTypeOptions(
        IntPtr licMgr, IntPtr dtm, [MarshalAs(UnmanagedType.LPWStr)] string path,
        IntPtr stream, [MarshalAs(UnmanagedType.LPWStr)] string? driverVer,
        [MarshalAs(UnmanagedType.LPWStr)] string? dtVer, TitleLoadHint hint, out TitleLoadResult result);

    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceId(IntPtr title);

    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_HasReverseInterlinear(IntPtr title);

    [DllImport(SinaiInterop)]
    static extern IntPtr CTitle_GetReverseInterlinearData(IntPtr title);

    // ReverseInterlinearData functions
    [DllImport(SinaiInterop)]
    static extern IntPtr ReverseInterlinearData_New(IntPtr licMgr, [MarshalAs(UnmanagedType.LPWStr)] string path);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string ReverseInterlinearData_ResourceIdToVersion(IntPtr rvi, [MarshalAs(UnmanagedType.LPWStr)] string resId);
    [DllImport(SinaiInterop)] static extern void ReverseInterlinearData_Delete(IntPtr rvi);

    // Interlinear functions
    [DllImport(SinaiInterop)]
    static extern IntPtr SinaiInterop_Interlinear_GetLabel(IntPtr interlinearLine);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_Interlinear_GetShowDefault(IntPtr interlinearLine);

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

            // TEST 1: ReverseInterlinearData_New + ResourceIdToVersion on ESVNT.lbsrvi
            Console.WriteLine("=== TEST 1: ReverseInterlinearData on ESVNT.lbsrvi ===");
            {
                string rviPath = $"{resourcesBase}/ESVNT.lbsrvi";
                IntPtr rvi = ReverseInterlinearData_New(licMgr, rviPath);
                Console.WriteLine($"  Created: {rvi != IntPtr.Zero}");
                if (rvi != IntPtr.Zero)
                {
                    // Now we know ESV.logos4 is LLS:1.0.710
                    // The RVI maps ESV words to original language (SBLGNT etc)
                    // ResourceIdToVersion might map original language resource IDs to their versions
                    string[] ids = {
                        // Known ESV resource ID
                        "LLS:1.0.710",
                        // Try common Greek NT resource IDs
                        "LLS:1.0.30", "LLS:1.0.62", "LLS:1.0.15",
                        "LLS:1.0.3", "LLS:1.0.4", "LLS:1.0.5",
                        "LLS:1.0.6", "LLS:1.0.7", "LLS:1.0.8",
                        "LLS:1.0.9", "LLS:1.0.10",
                        "LLS:1.0.20", "LLS:1.0.50", "LLS:1.0.100",
                        // Whole number ranges
                        "LLS:1.0.1", "LLS:1.0.2",
                        // SBLGNT and NA texts
                        "LLS:SBLGNT", "LLS:NA28", "LLS:NA27",
                        "LLS:BNT", "LLS:UBS5", "LLS:UBSGNT",
                        // Other formats
                        "SBLGNT", "NA28", "ESVNT",
                        "RVI:ESVNT", "DB:BIBLE-XREFS",
                    };
                    for (int i = 0; i < ids.Length; i++)
                    {
                        try
                        {
                            string ver = ReverseInterlinearData_ResourceIdToVersion(rvi, ids[i]);
                            string display = ver == null ? "(null)" : (ver.Length == 0 ? "(empty)" : ver);
                            Console.WriteLine($"    [{i:D2}] \"{ids[i]}\": {display}");
                        }
                        catch (Exception ex) { Console.WriteLine($"    [{i:D2}] \"{ids[i]}\": EXCEPTION {ex.Message}"); }
                    }
                    ReverseInterlinearData_Delete(rvi);
                }
            }

            // TEST 2: ReverseInterlinearData on NASBNT.lbsrvi
            Console.WriteLine("\n=== TEST 2: ReverseInterlinearData on NASBNT.lbsrvi ===");
            {
                string rviPath = $"{resourcesBase}/NASBNT.lbsrvi";
                IntPtr rvi = ReverseInterlinearData_New(licMgr, rviPath);
                Console.WriteLine($"  Created: {rvi != IntPtr.Zero}");
                if (rvi != IntPtr.Zero)
                {
                    string[] ids = { "LLS:1.0.710", "LLS:1.0.7", "LLS:1.0.30", "LLS:1.0.62",
                                      "LLS:1.0.1", "LLS:1.0.2", "LLS:1.0.3", "LLS:NASB", "NASBNT" };
                    foreach (string rid in ids)
                    {
                        try
                        {
                            string ver = ReverseInterlinearData_ResourceIdToVersion(rvi, rid);
                            string display = ver == null ? "(null)" : (ver.Length == 0 ? "(empty)" : ver);
                            Console.WriteLine($"    \"{rid}\": {display}");
                        }
                        catch { }
                    }
                    ReverseInterlinearData_Delete(rvi);
                }
            }

            // TEST 3: Load ESV.logos4 and check its RVI data pointer
            Console.WriteLine("\n=== TEST 3: CTitle RVI data from ESV.logos4 ===");
            {
                string esvPath = $"{resourcesBase}/ESV.logos4";
                IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                    licMgr, IntPtr.Zero, esvPath, IntPtr.Zero, null, null,
                    TitleLoadHint.Normal, out TitleLoadResult result);
                Console.WriteLine($"  Load: {result}");
                if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                {
                    string rid = SinaiInterop_CTitle_GetResourceId(title);
                    Console.WriteLine($"  ResourceId: {rid}");
                    Console.WriteLine($"  HasReverseInterlinear: {CTitle_HasReverseInterlinear(title)}");

                    IntPtr rviData = CTitle_GetReverseInterlinearData(title);
                    Console.WriteLine($"  RVI data ptr: {rviData}");
                    if (rviData != IntPtr.Zero)
                    {
                        // This rviData pointer is a CReverseInterlinearData* or similar
                        // Let's try to use it with ResourceIdToVersion
                        Console.WriteLine("  Trying ResourceIdToVersion on CTitle's RVI data:");
                        string[] ids = { "LLS:1.0.710", "LLS:1.0.30", "LLS:1.0.62", "SBLGNT" };
                        foreach (string id in ids)
                        {
                            try
                            {
                                string ver = ReverseInterlinearData_ResourceIdToVersion(rviData, id);
                                Console.WriteLine($"    \"{id}\": \"{ver ?? "(null)"}\"");
                            }
                            catch (Exception ex) { Console.WriteLine($"    \"{id}\": EXCEPTION {ex.Message}"); }
                        }
                    }
                }
            }

            // TEST 4: List some .logos4 files to find known resource IDs
            Console.WriteLine("\n=== TEST 4: Sample of .logos4 resource IDs ===");
            {
                var dir = new System.IO.DirectoryInfo(resourcesBase);
                int count = 0;
                foreach (var f in dir.GetFiles("*.logos4"))
                {
                    if (count >= 10) break;
                    IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                        licMgr, IntPtr.Zero, f.FullName, IntPtr.Zero, null, null,
                        TitleLoadHint.Normal, out TitleLoadResult result);
                    if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                    {
                        string rid = SinaiInterop_CTitle_GetResourceId(title);
                        bool hasRvi = false;
                        try { hasRvi = CTitle_HasReverseInterlinear(title); } catch { }
                        Console.WriteLine($"  {f.Name}: {rid} (hasRVI={hasRvi})");
                        count++;
                    }
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
