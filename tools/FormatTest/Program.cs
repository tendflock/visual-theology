using System;
using System.Runtime.InteropServices;

namespace FormatTest;

/// <summary>
/// Test program to explore whether non-.logos4 format files can be opened
/// via EncryptedVolume or SinaiInterop_LoadTitle APIs.
///
/// Tests: .lbslcr (cross-refs), .lbslms (lemmas), .lbsrvi (reverse interlinear)
/// </summary>
class Program
{
    const string SinaiInterop = "/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/Resources/lib/libSinaiInterop.dylib";

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void ManagedDebuggerBreakDelegate();

    enum TitleLoadHint : int { Normal = 0, Lite = 1, Indexing = 2 }
    enum TitleLoadResult : int { Failed = 0, Locked = 1, VersionIncompatible = 2, Success = 3 }

    // Library init
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LogosLibraryInitializationWrapper_Initialize(ManagedDebuggerBreakDelegate pfnManagedDebuggerBreak);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LogosLibraryInitializationWrapper_Uninitialize();

    // License manager
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr LicenseManagerCore_New(
        [MarshalAs(UnmanagedType.LPWStr)] string logosUserId,
        [MarshalAs(UnmanagedType.LPWStr)] string path);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LicenseManagerCore_LoadCore(IntPtr ptr);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LicenseManagerCore_Delete(IntPtr ptr);

    // Resource ID/Version probe (works without opening the title)
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_TryGetResourceIdAndVersion(
        IntPtr pLicenseManager,
        [MarshalAs(UnmanagedType.LPWStr)] string pszFilePath,
        [MarshalAs(UnmanagedType.LPWStr)] out string strResourceId,
        [MarshalAs(UnmanagedType.LPWStr)] out string strResourceVersion);

    // LoadTitle (with DataTypeOptionsCallback)
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_LoadTitle(
        IntPtr licenseManager,
        IntPtr dataTypeManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath,
        IntPtr pStream,
        [MarshalAs(UnmanagedType.LPWStr)] string? latestDriverVersion,
        [MarshalAs(UnmanagedType.LPWStr)] string? latestDataTypesVersion,
        TitleLoadHint loadHint,
        IntPtr dataTypeOptionsCallback,  // ISinaiDataTypeOptionsCallback*
        out TitleLoadResult result);

    // LoadTitleWithoutDataTypeOptions
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_LoadTitleWithoutDataTypeOptions(
        IntPtr licenseManager,
        IntPtr dataTypeManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath,
        IntPtr pStream,
        [MarshalAs(UnmanagedType.LPWStr)] string? latestDriverVersion,
        [MarshalAs(UnmanagedType.LPWStr)] string? latestDataTypesVersion,
        TitleLoadHint loadHint,
        out TitleLoadResult result);

    // EncryptedVolume functions
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_New();

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool EncryptedVolume_Open(
        IntPtr volume,
        IntPtr licenseManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetResourceId(IntPtr volume);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetResourceVersion(IntPtr volume);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetResourceDriverName(IntPtr volume);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetResourceDriverVersion(IntPtr volume);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetDataTypesRequiredVersion(IntPtr volume);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_OpenFile(
        IntPtr volume,
        [MarshalAs(UnmanagedType.LPWStr)] string fileName);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_OpenDatabase(
        IntPtr volume,
        [MarshalAs(UnmanagedType.LPWStr)] string databaseName);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_CreateConnectionStringDataSource(
        IntPtr volume,
        [MarshalAs(UnmanagedType.LPWStr)] string databaseName);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void EncryptedVolume_Delete(IntPtr volume);

    // CLibronixFile functions
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr CLibronixFile_OpenFile(
        IntPtr licenseManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool CLibronixFile_IsOpen(IntPtr file);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr CLibronixFile_OpenStream(
        IntPtr file,
        [MarshalAs(UnmanagedType.LPWStr)] string streamName);

    // CTitle functions we need
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_IsArticle(IntPtr title, int nArticle);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_ArticleNumberToArticleId(
        IntPtr title, int nArticle,
        [MarshalAs(UnmanagedType.LPWStr)] out string strArticleID);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_GetExactText(
        IntPtr title, int nArticle, int nStart, int nEnd,
        [MarshalAs(UnmanagedType.LPWStr)] out string strExactText);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern int SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(
        IntPtr title, int nArticle,
        [MarshalAs(UnmanagedType.U1)] bool bIncludeFullArticleText);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceId(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceVersion(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceDriverVersion(IntPtr title);

    // GetSupportedDriverVersions
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_GetSupportedDriverVersions(
        [MarshalAs(UnmanagedType.LPWStr)] string driverName);

    // ReverseInterlinearData
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr ReverseInterlinearData_New(
        IntPtr licenseManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void ReverseInterlinearData_Delete(IntPtr rviData);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string ReverseInterlinearData_ResourceIdToVersion(
        IntPtr rviData,
        [MarshalAs(UnmanagedType.LPWStr)] string resourceId);

    static ManagedDebuggerBreakDelegate s_debugBreakDelegate = OnDebugBreak;
    static void OnDebugBreak() { Console.Error.WriteLine("[Native assertion failed]"); }

    static void Main(string[] args)
    {
        string userId = "5621617";
        string licenseFolder = "/Volumes/External/Logos4/Data/e3txalek.5iq/LicenseManager";
        string resourcesBase = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources";

        string[] testFiles = args.Length > 0 ? args : new[] { "BIBLEXREFS.lbslcr", "Lemmas.lbslms", "ESVNT.lbsrvi" };

        Console.WriteLine("=== Logos Format Test ===");
        Console.WriteLine();

        try
        {
            Console.WriteLine("[INIT] Initializing native library...");
            LogosLibraryInitializationWrapper_Initialize(s_debugBreakDelegate);

            Console.WriteLine("[INIT] Creating license manager...");
            IntPtr licMgr = LicenseManagerCore_New(userId, licenseFolder);
            if (licMgr == IntPtr.Zero)
            {
                Console.WriteLine("[FAIL] License manager creation failed");
                return;
            }
            LicenseManagerCore_LoadCore(licMgr);
            Console.WriteLine("[INIT] License manager ready.");
            Console.WriteLine();

            foreach (string file in testFiles)
            {
                string fullPath = file.Contains("/") ? file : $"{resourcesBase}/{file}";
                string fileName = System.IO.Path.GetFileName(fullPath);
                string ext = System.IO.Path.GetExtension(fullPath);

                Console.WriteLine($"========================================");
                Console.WriteLine($"FILE: {fileName}");
                Console.WriteLine($"SIZE: {new System.IO.FileInfo(fullPath).Length / 1024 / 1024} MB");
                Console.WriteLine($"========================================");

                // Test 1: TryGetResourceIdAndVersion
                Console.WriteLine();
                Console.WriteLine("--- Test 1: TryGetResourceIdAndVersion ---");
                try
                {
                    bool ok = SinaiInterop_TryGetResourceIdAndVersion(licMgr, fullPath, out string resId, out string resVer);
                    Console.WriteLine($"  Result: {(ok ? "SUCCESS" : "FAILED")}");
                    if (ok)
                    {
                        Console.WriteLine($"  ResourceId: {resId}");
                        Console.WriteLine($"  Version: {resVer}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  EXCEPTION: {ex.GetType().Name}: {ex.Message}");
                }

                // Test 2: LoadTitleWithoutDataTypeOptions (all hints)
                Console.WriteLine();
                Console.WriteLine("--- Test 2: LoadTitleWithoutDataTypeOptions ---");
                foreach (var hint in new[] { TitleLoadHint.Normal, TitleLoadHint.Lite, TitleLoadHint.Indexing })
                {
                    try
                    {
                        IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
                            licMgr, IntPtr.Zero, fullPath, IntPtr.Zero, null, null, hint, out TitleLoadResult result);
                        Console.WriteLine($"  hint={hint}: result={result}, ptr={title != IntPtr.Zero}");
                        if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                        {
                            string rid = SinaiInterop_CTitle_GetResourceId(title);
                            string rver = SinaiInterop_CTitle_GetResourceVersion(title);
                            string dver = SinaiInterop_CTitle_GetResourceDriverVersion(title);
                            Console.WriteLine($"    ResourceId={rid}, Version={rver}, Driver={dver}");

                            // Count articles
                            int count = 0;
                            for (int i = 0; i < 200000; i++)
                            {
                                if (!SinaiInterop_CTitle_IsArticle(title, i)) break;
                                count++;
                            }
                            Console.WriteLine($"    ArticleCount={count}");

                            // Read first 3 articles
                            for (int i = 0; i < Math.Min(3, count); i++)
                            {
                                SinaiInterop_CTitle_ArticleNumberToArticleId(title, i, out string artId);
                                int start = SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(title, i, false);
                                int end = SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(title, i, true);
                                Console.WriteLine($"    Article[{i}]: id={artId}, chars={end - start}");
                                if (SinaiInterop_CTitle_GetExactText(title, i, 0, Math.Min(500, end - start), out string text))
                                {
                                    string preview = text.Length > 200 ? text.Substring(0, 200) + "..." : text;
                                    Console.WriteLine($"      Text: {preview}");
                                }
                            }
                            break; // Don't try other hints if this worked
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"  hint={hint}: EXCEPTION: {ex.GetType().Name}: {ex.Message}");
                    }
                }

                // Test 3: SinaiInterop_LoadTitle (with null callback)
                Console.WriteLine();
                Console.WriteLine("--- Test 3: SinaiInterop_LoadTitle (null callback) ---");
                try
                {
                    IntPtr title = SinaiInterop_LoadTitle(
                        licMgr, IntPtr.Zero, fullPath, IntPtr.Zero, null, null,
                        TitleLoadHint.Normal, IntPtr.Zero, out TitleLoadResult result);
                    Console.WriteLine($"  result={result}, ptr={title != IntPtr.Zero}");
                    if (result == TitleLoadResult.Success && title != IntPtr.Zero)
                    {
                        string rid = SinaiInterop_CTitle_GetResourceId(title);
                        Console.WriteLine($"  ResourceId={rid}");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  EXCEPTION: {ex.GetType().Name}: {ex.Message}");
                }

                // Test 4: EncryptedVolume_Open
                Console.WriteLine();
                Console.WriteLine("--- Test 4: EncryptedVolume ---");
                try
                {
                    IntPtr vol = EncryptedVolume_New();
                    Console.WriteLine($"  Volume created: {vol != IntPtr.Zero}");
                    if (vol != IntPtr.Zero)
                    {
                        bool opened = EncryptedVolume_Open(vol, licMgr, fullPath);
                        Console.WriteLine($"  Open: {(opened ? "SUCCESS" : "FAILED")}");
                        if (opened)
                        {
                            string volResId = EncryptedVolume_GetResourceId(vol);
                            string volResVer = EncryptedVolume_GetResourceVersion(vol);
                            string driverName = EncryptedVolume_GetResourceDriverName(vol);
                            string driverVer = EncryptedVolume_GetResourceDriverVersion(vol);
                            string dtVer = EncryptedVolume_GetDataTypesRequiredVersion(vol);
                            Console.WriteLine($"  ResourceId: {volResId}");
                            Console.WriteLine($"  Version: {volResVer}");
                            Console.WriteLine($"  DriverName: {driverName}");
                            Console.WriteLine($"  DriverVersion: {driverVer}");
                            Console.WriteLine($"  DataTypesRequired: {dtVer}");

                            // Try to open internal files
                            Console.WriteLine();
                            Console.WriteLine("  --- Trying internal files/databases ---");
                            string[] tryFiles = { "data", "index", "content", "articles", "metadata",
                                                   "xrefs", "lemmas", "interlinear", "main",
                                                   "data.db", "content.db" };
                            foreach (string tryFile in tryFiles)
                            {
                                try
                                {
                                    IntPtr stream = EncryptedVolume_OpenFile(vol, tryFile);
                                    if (stream != IntPtr.Zero)
                                        Console.WriteLine($"    OpenFile(\"{tryFile}\"): GOT STREAM {stream}");
                                }
                                catch { }

                                try
                                {
                                    IntPtr db = EncryptedVolume_OpenDatabase(vol, tryFile);
                                    if (db != IntPtr.Zero)
                                        Console.WriteLine($"    OpenDatabase(\"{tryFile}\"): GOT DB {db}");
                                }
                                catch { }
                            }

                            // Try ConnectionStringDataSource
                            foreach (string tryDb in tryFiles)
                            {
                                try
                                {
                                    IntPtr ds = EncryptedVolume_CreateConnectionStringDataSource(vol, tryDb);
                                    if (ds != IntPtr.Zero)
                                        Console.WriteLine($"    CreateConnectionStringDataSource(\"{tryDb}\"): GOT DS {ds}");
                                }
                                catch { }
                            }
                        }
                        EncryptedVolume_Delete(vol);
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  EXCEPTION: {ex.GetType().Name}: {ex.Message}");
                }

                // Test 5: CLibronixFile_OpenFile
                Console.WriteLine();
                Console.WriteLine("--- Test 5: CLibronixFile ---");
                try
                {
                    IntPtr lbxFile = CLibronixFile_OpenFile(licMgr, fullPath);
                    Console.WriteLine($"  OpenFile: ptr={lbxFile != IntPtr.Zero}");
                    if (lbxFile != IntPtr.Zero)
                    {
                        bool isOpen = CLibronixFile_IsOpen(lbxFile);
                        Console.WriteLine($"  IsOpen: {isOpen}");

                        if (isOpen)
                        {
                            string[] streams = { "", "content", "data", "articles", "metadata", "main" };
                            foreach (string s in streams)
                            {
                                try
                                {
                                    IntPtr stream = CLibronixFile_OpenStream(lbxFile, s);
                                    if (stream != IntPtr.Zero)
                                        Console.WriteLine($"    Stream(\"{s}\"): GOT STREAM {stream}");
                                }
                                catch { }
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  EXCEPTION: {ex.GetType().Name}: {ex.Message}");
                }

                // Test 6: ReverseInterlinearData (for .lbsrvi files)
                if (ext == ".lbsrvi")
                {
                    Console.WriteLine();
                    Console.WriteLine("--- Test 6: ReverseInterlinearData ---");
                    try
                    {
                        IntPtr rvi = ReverseInterlinearData_New(licMgr, fullPath);
                        Console.WriteLine($"  Created: {rvi != IntPtr.Zero}");
                        if (rvi != IntPtr.Zero)
                        {
                            // Try to get version for some resource IDs
                            string[] resourceIds = { "LLS:ESV", "LLS:1.0.6", "bible.esv", "ESV" };
                            foreach (string rid in resourceIds)
                            {
                                try
                                {
                                    string ver = ReverseInterlinearData_ResourceIdToVersion(rvi, rid);
                                    if (ver != null)
                                        Console.WriteLine($"    ResourceIdToVersion(\"{rid}\"): {ver}");
                                }
                                catch { }
                            }
                            ReverseInterlinearData_Delete(rvi);
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"  EXCEPTION: {ex.GetType().Name}: {ex.Message}");
                    }
                }

                Console.WriteLine();
            }

            LogosLibraryInitializationWrapper_Uninitialize();
            LicenseManagerCore_Delete(licMgr);
            Console.WriteLine("[DONE] All tests complete.");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[FATAL] {ex.GetType().Name}: {ex.Message}");
            Console.WriteLine(ex.StackTrace);
        }
    }
}
