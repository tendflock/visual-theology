using System;
using System.Runtime.InteropServices;

namespace FormatTest5;

/// <summary>
/// Test 5: Explore CInterlinearData and CTitle interlinear/RVI accessors.
/// Focus on extracting actual interlinear and reverse interlinear data from loaded titles.
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
    static extern bool SinaiInterop_CTitle_IsArticle(IntPtr title, int article);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_ArticleNumberToArticleId(IntPtr title, int article, [MarshalAs(UnmanagedType.LPWStr)] out string artId);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_GetExactText(IntPtr title, int article, int start, int end, [MarshalAs(UnmanagedType.LPWStr)] out string text);
    [DllImport(SinaiInterop)]
    static extern int SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(IntPtr title, int article, [MarshalAs(UnmanagedType.U1)] bool includeAll);

    // CTitle properties
    [DllImport(SinaiInterop)] static extern int CTitle_GetArticleCount(IntPtr title);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)] static extern bool CTitle_HasReverseInterlinear(IntPtr title);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)] static extern bool CTitle_HasInterlinear(IntPtr title);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)] static extern bool CTitle_IsBible(IntPtr title);
    [DllImport(SinaiInterop)] static extern IntPtr CTitle_GetReverseInterlinearData(IntPtr title);
    [DllImport(SinaiInterop)] static extern IntPtr CTitle_GetInterlinearData(IntPtr title);

    // CInterlinearData
    [DllImport(SinaiInterop)]
    static extern IntPtr CInterlinearData_New(IntPtr licenseManager, [MarshalAs(UnmanagedType.LPWStr)] string filePath);
    [DllImport(SinaiInterop)] static extern int CInterlinearData_GetLineCount(IntPtr intData);
    [DllImport(SinaiInterop)] static extern IntPtr CInterlinearData_GetLine(IntPtr intData, int lineIndex);
    [DllImport(SinaiInterop)] static extern void CInterlinearData_Delete(IntPtr intData);

    // InterlinearLine
    [DllImport(SinaiInterop)] static extern IntPtr InterlinearLine_New();
    [DllImport(SinaiInterop)] static extern void InterlinearLine_Delete(IntPtr line);

    // SinaiInterop Interlinear accessors
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_Interlinear_GetLabel(IntPtr interlinearLine);
    [DllImport(SinaiInterop)][return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_Interlinear_GetShowDefault(IntPtr interlinearLine);

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
            LogosLibraryInitializationWrapper_Initialize(s_debugBreak);
            IntPtr licMgr = LicenseManagerCore_New(userId, licenseFolder);
            LicenseManagerCore_LoadCore(licMgr);
            Console.WriteLine("[INIT] Ready.\n");

            // TEST 1: Load ESV.logos4 and explore its interlinear data structure
            Console.WriteLine("=== TEST 1: ESV.logos4 Interlinear Data ===");
            {
                string esvPath = $"{resourcesBase}/ESV.logos4";
                IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                    licMgr, IntPtr.Zero, esvPath, IntPtr.Zero, null, null,
                    TitleLoadHint.Normal, out TitleLoadResult result);

                if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                {
                    Console.WriteLine($"  ResourceId: {SinaiInterop_CTitle_GetResourceId(title)}");
                    Console.WriteLine($"  IsBible: {CTitle_IsBible(title)}");

                    try
                    {
                        int artCount = CTitle_GetArticleCount(title);
                        Console.WriteLine($"  ArticleCount: {artCount}");
                    }
                    catch (Exception ex) { Console.WriteLine($"  ArticleCount: EXCEPTION {ex.Message}"); }

                    Console.WriteLine($"  HasInterlinear: {CTitle_HasInterlinear(title)}");
                    Console.WriteLine($"  HasReverseInterlinear: {CTitle_HasReverseInterlinear(title)}");

                    // Get interlinear data from the title
                    IntPtr intData = CTitle_GetInterlinearData(title);
                    Console.WriteLine($"  GetInterlinearData: {(intData != IntPtr.Zero ? $"ptr={intData}" : "null")}");

                    if (intData != IntPtr.Zero)
                    {
                        try
                        {
                            int lineCount = CInterlinearData_GetLineCount(intData);
                            Console.WriteLine($"  InterlinearData.LineCount: {lineCount}");

                            for (int i = 0; i < Math.Min(lineCount, 10); i++)
                            {
                                IntPtr line = CInterlinearData_GetLine(intData, i);
                                if (line != IntPtr.Zero)
                                {
                                    try
                                    {
                                        string label = SinaiInterop_Interlinear_GetLabel(line);
                                        bool showDefault = SinaiInterop_Interlinear_GetShowDefault(line);
                                        Console.WriteLine($"    Line[{i}]: label=\"{label ?? "(null)"}\", showDefault={showDefault}");
                                    }
                                    catch (Exception ex) { Console.WriteLine($"    Line[{i}]: EXCEPTION {ex.Message}"); }
                                }
                                else
                                {
                                    Console.WriteLine($"    Line[{i}]: null");
                                }
                            }
                        }
                        catch (Exception ex) { Console.WriteLine($"  InterlinearData error: {ex.Message}"); }
                    }

                    // Get RVI data from the title
                    IntPtr rviData = CTitle_GetReverseInterlinearData(title);
                    Console.WriteLine($"\n  GetReverseInterlinearData: {(rviData != IntPtr.Zero ? $"ptr={rviData}" : "null")}");

                    // Check: are intData and rviData the same pointer?
                    if (intData != IntPtr.Zero && rviData != IntPtr.Zero)
                    {
                        Console.WriteLine($"  Same pointer as InterlinearData? {intData == rviData}");
                    }
                }
                else
                {
                    Console.WriteLine($"  Load failed: {result}");
                }
            }

            // TEST 2: Try CInterlinearData_New with .lbsrvi file path
            Console.WriteLine("\n=== TEST 2: CInterlinearData_New on .lbsrvi ===");
            {
                string rviPath = $"{resourcesBase}/ESVNT.lbsrvi";
                try
                {
                    IntPtr intData = CInterlinearData_New(licMgr, rviPath);
                    Console.WriteLine($"  CInterlinearData_New(ESVNT.lbsrvi): {(intData != IntPtr.Zero ? $"ptr={intData}" : "null")}");
                    if (intData != IntPtr.Zero)
                    {
                        int lineCount = CInterlinearData_GetLineCount(intData);
                        Console.WriteLine($"    LineCount: {lineCount}");
                        for (int i = 0; i < Math.Min(lineCount, 10); i++)
                        {
                            IntPtr line = CInterlinearData_GetLine(intData, i);
                            if (line != IntPtr.Zero)
                            {
                                string label = SinaiInterop_Interlinear_GetLabel(line);
                                Console.WriteLine($"    Line[{i}]: \"{label}\"");
                            }
                        }
                        CInterlinearData_Delete(intData);
                    }
                }
                catch (Exception ex) { Console.WriteLine($"  EXCEPTION: {ex.Message}"); }
            }

            // TEST 3: Try CInterlinearData_New with .lbslms file path
            Console.WriteLine("\n=== TEST 3: CInterlinearData_New on .lbslms ===");
            {
                string lemmaPath = $"{resourcesBase}/Lemmas.lbslms";
                try
                {
                    IntPtr intData = CInterlinearData_New(licMgr, lemmaPath);
                    Console.WriteLine($"  CInterlinearData_New(Lemmas.lbslms): {(intData != IntPtr.Zero ? $"ptr={intData}" : "null")}");
                    if (intData != IntPtr.Zero)
                    {
                        int lineCount = CInterlinearData_GetLineCount(intData);
                        Console.WriteLine($"    LineCount: {lineCount}");
                        CInterlinearData_Delete(intData);
                    }
                }
                catch (Exception ex) { Console.WriteLine($"  EXCEPTION: {ex.Message}"); }
            }

            // TEST 4: Try CInterlinearData_New on .lbslcr file
            Console.WriteLine("\n=== TEST 4: CInterlinearData_New on .lbslcr ===");
            {
                string xrefPath = $"{resourcesBase}/BIBLEXREFS.lbslcr";
                try
                {
                    IntPtr intData = CInterlinearData_New(licMgr, xrefPath);
                    Console.WriteLine($"  CInterlinearData_New(BIBLEXREFS.lbslcr): {(intData != IntPtr.Zero ? $"ptr={intData}" : "null")}");
                    if (intData != IntPtr.Zero)
                    {
                        int lineCount = CInterlinearData_GetLineCount(intData);
                        Console.WriteLine($"    LineCount: {lineCount}");
                        CInterlinearData_Delete(intData);
                    }
                }
                catch (Exception ex) { Console.WriteLine($"  EXCEPTION: {ex.Message}"); }
            }

            // TEST 5: ReverseInterlinearData_New on .lbsrvi and try to understand what it provides
            Console.WriteLine("\n=== TEST 5: ReverseInterlinearData on ESVNT.lbsrvi ===");
            {
                string rviPath = $"{resourcesBase}/ESVNT.lbsrvi";
                IntPtr rvi = ReverseInterlinearData_New(licMgr, rviPath);
                Console.WriteLine($"  ReverseInterlinearData_New: {(rvi != IntPtr.Zero ? $"ptr={rvi}" : "null")}");
                if (rvi != IntPtr.Zero)
                {
                    // Read bytes at the pointer to understand the object structure
                    Console.WriteLine("  Object memory layout (first 128 bytes):");
                    for (int offset = 0; offset < 128; offset += 8)
                    {
                        try
                        {
                            long val = Marshal.ReadInt64(rvi + offset);
                            Console.WriteLine($"    +{offset:D3}: 0x{val:X16} ({val})");
                        }
                        catch { break; }
                    }
                    ReverseInterlinearData_Delete(rvi);
                }
            }

            // TEST 6: List all Bible .logos4 files and check which have RVI
            Console.WriteLine("\n=== TEST 6: Bible files with ReverseInterlinear ===");
            {
                var dir = new System.IO.DirectoryInfo(resourcesBase);
                int found = 0;
                foreach (var f in dir.GetFiles("*.logos4"))
                {
                    IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                        licMgr, IntPtr.Zero, f.FullName, IntPtr.Zero, null, null,
                        TitleLoadHint.Normal, out TitleLoadResult result);
                    if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                    {
                        try
                        {
                            if (CTitle_IsBible(title))
                            {
                                bool hasRvi = CTitle_HasReverseInterlinear(title);
                                bool hasInt = CTitle_HasInterlinear(title);
                                string rid = SinaiInterop_CTitle_GetResourceId(title);
                                if (hasRvi || hasInt)
                                {
                                    Console.WriteLine($"  {f.Name}: {rid} (rvi={hasRvi}, interlinear={hasInt})");
                                    found++;
                                }
                            }
                        }
                        catch { }
                    }
                    if (found >= 15) break;
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
