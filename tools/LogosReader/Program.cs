using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

namespace LogosReader;

class Program
{
    // Native library path
    const string SinaiInterop = "/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/Resources/lib/libSinaiInterop.dylib";

    // Delegates
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void ManagedDebuggerBreakDelegate();

    // Enums
    enum TitleLoadHint : int
    {
        Normal = 0,
        Lite = 1,
        Indexing = 2
    }

    enum TitleLoadResult : int
    {
        Failed = 0,
        Locked = 1,
        VersionIncompatible = 2,
        Success = 3
    }

    // P/Invoke declarations - License Manager
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LogosLibraryInitializationWrapper_Initialize(ManagedDebuggerBreakDelegate pfnManagedDebuggerBreak);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LogosLibraryInitializationWrapper_Uninitialize();

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr LicenseManagerCore_New(
        [MarshalAs(UnmanagedType.LPWStr)] string logosUserId,
        [MarshalAs(UnmanagedType.LPWStr)] string path);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LicenseManagerCore_LoadCore(IntPtr ptr);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool LicenseManagerCore_IsFeatureUnlockedCore(IntPtr ptr,
        [MarshalAs(UnmanagedType.LPWStr)] string strCommerceId);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void LicenseManagerCore_Delete(IntPtr ptr);

    // P/Invoke declarations - Resource Loading
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_LoadTitleWithoutDataTypeOptions(
        IntPtr licenseManager,
        IntPtr dataTypeManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath,
        IntPtr pStream,
        [MarshalAs(UnmanagedType.LPWStr)] string latestDriverVersion,
        [MarshalAs(UnmanagedType.LPWStr)] string latestDataTypesVersion,
        TitleLoadHint loadHint,
        out TitleLoadResult result);

    // P/Invoke declarations - Text Extraction
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_GetExactText(
        IntPtr title,
        int nArticle,
        int nStart,
        int nEnd,
        [MarshalAs(UnmanagedType.LPWStr)] out string strExactText);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_IsArticle(IntPtr title, int nArticle);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_ArticleNumberToArticleId(
        IntPtr title,
        int nArticle,
        [MarshalAs(UnmanagedType.LPWStr)] out string strArticleID);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern int SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(
        IntPtr title,
        int nArticle,
        [MarshalAs(UnmanagedType.U1)] bool bIncludeFullArticleText);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_CTitle_GetArticleOffsetFromPosition(
        IntPtr title,
        [MarshalAs(UnmanagedType.LPWStr)] string strPosition,
        out int nArticle,
        out int nOffset);

    // TOC functions
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern int SinaiInterop_CTitle_GetTOCRoot(IntPtr pTitle);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void SinaiInterop_CTitle_GetTOCEntryLabel(
        IntPtr pTitle,
        int nEntry,
        [MarshalAs(UnmanagedType.LPWStr)] out string strLabel);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_CTitle_GetTOCEntryChildren(IntPtr pTitle, int nEntry);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void SinaiInterop_CTitle_GetTOCLocation(
        IntPtr pTitle,
        int nEntry,
        out int nArticle,
        out int nOffset);

    // Resource info
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceId(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceVersion(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_CTitle_GetResourceDriverVersion(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_TryGetResourceIdAndVersion(
        IntPtr pLicenseManager,
        [MarshalAs(UnmanagedType.LPWStr)] string pszFilePath,
        [MarshalAs(UnmanagedType.LPWStr)] out string strResourceId,
        [MarshalAs(UnmanagedType.LPWStr)] out string strResourceVersion);

    // Interlinear data - CTitle accessors
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_HasInterlinear(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_HasReverseInterlinear(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool CTitle_IsBible(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr CTitle_GetInterlinearData(IntPtr title);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr CTitle_GetReverseInterlinearData(IntPtr title);

    // CInterlinearData
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern int CInterlinearData_GetLineCount(IntPtr intData);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr CInterlinearData_GetLine(IntPtr intData, int lineIndex);

    // InterlinearLine accessors
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string SinaiInterop_Interlinear_GetLabel(IntPtr interlinearLine);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool SinaiInterop_Interlinear_GetShowDefault(IntPtr interlinearLine);

    // ── EncryptedVolume API ──────────────────────────────────────────────
    // Opens encrypted dataset files (.lbssd, .lbsxrf, .lbsplc, .lbsthg, etc.)
    // These contain embedded SQLite databases with structured study tool data.

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_New();

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.U1)]
    static extern bool EncryptedVolume_Open(
        IntPtr ptr,
        IntPtr pLicenseManager,
        [MarshalAs(UnmanagedType.LPWStr)] string filePath);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_OpenDatabase(
        IntPtr ptr,
        [MarshalAs(UnmanagedType.LPWStr)] string strFileName);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr EncryptedVolume_OpenFile(
        IntPtr ptr,
        [MarshalAs(UnmanagedType.LPWStr)] string strFileName);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetResourceId(IntPtr ptr);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.LPWStr)]
    static extern string EncryptedVolume_GetResourceDriverName(IntPtr ptr);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void EncryptedVolume_Delete(IntPtr ptr);

    // ── SQLite C API (from libsqlite3-logos.dylib bundled with Logos) ────
    // Used to query the raw sqlite3* handle returned by EncryptedVolume_OpenDatabase.

    const string SqliteLib = "/Applications/Logos.app/Contents/Frameworks/FaithlifeDesktop.framework/Versions/48.0.0.0238/Frameworks/ApplicationBundle.framework/Resources/lib/libsqlite3-logos.dylib";

    [DllImport(SqliteLib, EntryPoint = "sqlite3_prepare_v2")]
    static extern int sqlite3_prepare_v2(IntPtr db, byte[] sql, int nByte, out IntPtr stmt, out IntPtr tail);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_step")]
    static extern int sqlite3_step(IntPtr stmt);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_column_count")]
    static extern int sqlite3_column_count(IntPtr stmt);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_column_name")]
    static extern IntPtr sqlite3_column_name(IntPtr stmt, int col);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_column_text")]
    static extern IntPtr sqlite3_column_text(IntPtr stmt, int col);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_column_type")]
    static extern int sqlite3_column_type(IntPtr stmt, int col);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_finalize")]
    static extern int sqlite3_finalize(IntPtr stmt);

    [DllImport(SqliteLib, EntryPoint = "sqlite3_errmsg")]
    static extern IntPtr sqlite3_errmsg(IntPtr db);

    // SQLite constants
    const int SQLITE_ROW = 100;
    const int SQLITE_DONE = 101;
    const int SQLITE_OK = 0;
    const int SQLITE_NULL = 5;

    // NativeLogosResourceIndexer - for extracting word-level interlinear data
    // Callback delegate types matching the C++ NativeLogosResourceIndexerCallbackImpl constructor
    // Signatures derived from mangled C++ symbol analysis:
    //   Constructor params (9 function pointers):
    //   1. void(*)(int)                                    - AddDefaultSectionStart
    //   2. void(*)(char16_t const*, int)                   - AddNamedSectionStart
    //   3. void(*)(char16_t const*, int)                   - AddNamedSectionEnd
    //   4. void(*)(Media, i,i,i,i, void*,i,i,i,i)         - AddMedia (10 params)
    //   5. void(*)(ptr,i,ptr,i,i,i,i,i,ptr,i,i,i,i)       - AddReference (13 params)
    //   6. void(*)(ptr,i,i,i,i,i,ptr,i,i,i,i)             - AddWord (11 params)
    //   7. void(*)(ptr,i,i,i,i,i,ptr,i,i,i,i)             - AddResourceJump (same as AddWord)
    //   8. void(*)(char16_t*, RICID*,int)                  - ProcessReverseInterlinearIndexData
    //   9. void(*)(char16_t const*)                        - SetLanguage

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void SetLanguageCallback(IntPtr language);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void AddDefaultSectionStartCallback(int offset);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void AddNamedSectionCallback(IntPtr name, int offset);

    // AddMedia: 10 params
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void AddMediaCallback(int mediaType, int a, int b, int c, int d, IntPtr data, int e, int f, int g, int h);

    // AddReference: 13 params
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void AddReferenceCallback(
        IntPtr ref1, int offset,
        IntPtr ref2, int a, int b, int c, int d, int e,
        IntPtr ref3, int f, int g, int h, int i);

    // AddWord: 11 params
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void AddWordCallback(
        IntPtr word, int a, int b, int c, int d, int e,
        IntPtr word2, int f, int g, int h, int i2);

    // ProcessReverseInterlinearIndexData: 3 params
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate void ProcessReverseInterlinearIndexDataCallback(
        IntPtr word, IntPtr columnData, int columnCount);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr NativeLogosResourceIndexerCallbackImpl_New(
        IntPtr addDefaultSectionStart,    // 1. void(*)(int)
        IntPtr addNamedSectionStart,      // 2. void(*)(char16_t const*, int)
        IntPtr addNamedSectionEnd,        // 3. void(*)(char16_t const*, int)
        IntPtr addMedia,                  // 4. void(*)(Media, i*4, void*, i*4)
        IntPtr addReference,              // 5. void(*)(ptr, i, ptr, i*5, ptr, i*4) - 13 params
        IntPtr addWord,                   // 6. void(*)(ptr, i*5, ptr, i*4) - 11 params
        IntPtr addResourceJump,           // 7. same as AddWord - 11 params
        IntPtr processReverseInterlinear, // 8. void(*)(char16_t*, RICID*, int)
        IntPtr setLanguage                // 9. void(*)(char16_t const*)
    );

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void NativeLogosResourceIndexerCallbackImpl_Delete(IntPtr callback);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr NativeLogosResourceIndexer_New(IntPtr title, IntPtr callback);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void NativeLogosResourceIndexer_IndexArticle(IntPtr indexer, int article);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void NativeLogosResourceIndexer_FinishIndexing(IntPtr indexer);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void NativeLogosResourceIndexer_Delete(IntPtr indexer);

    // Navigation index - maps Bible references to article positions
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    [return: MarshalAs(UnmanagedType.U1)]
    delegate bool NavIndexReferenceCallback(IntPtr reference, uint article, uint offset);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    [return: MarshalAs(UnmanagedType.U1)]
    delegate bool NavIndexTopicCallback(IntPtr key, IntPtr name, uint article, uint offset);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr ManagedNavigationIndexVisitor_New(
        IntPtr onReferenceItem,
        IntPtr onTopicItem);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void ManagedNavigationIndexVisitor_Delete(IntPtr visitor);

    // Extract Sinai::Resource from CTitle (needed for ResourceVolume)
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr CTitle_GetResource(IntPtr pTitle);

    // ResourceVolume - needed for ExportNavigationIndex and GetArticleTitle
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern IntPtr SinaiInterop_ResourceVolumeFromResource(IntPtr pResource);

    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void SinaiInterop_ExportNavigationIndex(
        IntPtr title,
        IntPtr resourceVolume,
        IntPtr visitor);

    // Article title - gets proper title for an article
    [DllImport(SinaiInterop, CharSet = CharSet.Ansi, ExactSpelling = true)]
    static extern void SinaiInterop_GetArticleTitle(
        IntPtr title,
        IntPtr resourceVolume,
        uint articleNum,
        [MarshalAs(UnmanagedType.LPWStr)] out string articleTitle);

    static ManagedDebuggerBreakDelegate s_debugBreakDelegate = OnDebugBreak;

    static void OnDebugBreak()
    {
        Console.Error.WriteLine("[Native assertion failed]");
    }

    static void Main(string[] args)
    {
        string userId = "5621617";
        string licenseFolder = "/Volumes/External/Logos4/Data/e3txalek.5iq/LicenseManager";
        string resourcesBase = "/Volumes/External/Logos4/Data/e3txalek.5iq/ResourceManager/Resources";

        if (args.Length < 1)
        {
            Console.WriteLine("LogosReader - Extract text from Logos Bible Software resources");
            Console.WriteLine();
            Console.WriteLine("Usage:");
            Console.WriteLine("  LogosReader <file> [article#] [max-chars]       Read article text");
            Console.WriteLine("  LogosReader --list <file>                       List all articles");
            Console.WriteLine("  LogosReader --toc <file>                        Show table of contents");
            Console.WriteLine("  LogosReader --info <file>                       Show resource info");
            Console.WriteLine("  LogosReader --find-article <file> <pattern>     Find articles matching pattern");
            Console.WriteLine("  LogosReader --interlinear <file> <article#>     Extract interlinear data");
            Console.WriteLine("  LogosReader --navindex <file>                   Export navigation index (ref→article map)");
            Console.WriteLine("  LogosReader --article-title <file> <article#>   Get article title");
            Console.WriteLine("  LogosReader --batch                             Batch mode (read commands from stdin)");
            Console.WriteLine();
            Console.WriteLine("Batch mode commands (one per line on stdin):");
            Console.WriteLine("  read <file> <article#> <max-chars>");
            Console.WriteLine("  list <file>");
            Console.WriteLine("  info <file>");
            Console.WriteLine("  toc <file>");
            Console.WriteLine("  find-article <file> <pattern>");
            Console.WriteLine("  interlinear <file> <article#>");
            Console.WriteLine("  navindex <file>");
            Console.WriteLine("  article-title <file> <article#>");
            Console.WriteLine("Each result is delimited by a line containing only '---END---'.");
            Console.WriteLine("Empty line or EOF exits batch mode.");
            Console.WriteLine();
            Console.WriteLine("Examples:");
            Console.WriteLine("  LogosReader KJV1900.logos4");
            Console.WriteLine("  LogosReader KJV1900.logos4 0 5000");
            Console.WriteLine("  LogosReader --list MORNEVE.logos4");
            Console.WriteLine("  LogosReader --find-article MORNEVE.logos4 \"Gen 1\"");
            Console.WriteLine("  LogosReader --interlinear ESV.logos4 0");
            return;
        }

        // Check for batch mode first
        if (args[0] == "--batch")
        {
            RunBatchMode(resourcesBase, userId, licenseFolder);
            return;
        }

        string mode = "read";
        string resourceFile = args[0];
        int articleNum = 0;
        int maxChars = 10000;
        string findPattern = null;

        if (args[0] == "--list" && args.Length >= 2)
        {
            mode = "list";
            resourceFile = args[1];
        }
        else if (args[0] == "--toc" && args.Length >= 2)
        {
            mode = "toc";
            resourceFile = args[1];
        }
        else if (args[0] == "--info" && args.Length >= 2)
        {
            mode = "info";
            resourceFile = args[1];
        }
        else if (args[0] == "--interlinear" && args.Length >= 3)
        {
            mode = "interlinear";
            resourceFile = args[1];
            if (args.Length >= 3) int.TryParse(args[2], out articleNum);
        }
        else if (args[0] == "--navindex" && args.Length >= 2)
        {
            mode = "navindex";
            resourceFile = args[1];
        }
        else if (args[0] == "--article-title" && args.Length >= 3)
        {
            mode = "article-title";
            resourceFile = args[1];
            int.TryParse(args[2], out articleNum);
        }
        else if (args[0] == "--find-article" && args.Length >= 3)
        {
            mode = "find-article";
            resourceFile = args[1];
            findPattern = args[2];
        }
        else
        {
            if (args.Length >= 2) int.TryParse(args[1], out articleNum);
            if (args.Length >= 3) int.TryParse(args[2], out maxChars);
        }

        if (!resourceFile.Contains("/"))
            resourceFile = $"{resourcesBase}/{resourceFile}";

        Console.Error.WriteLine("[*] Initializing Logos native library...");

        try
        {
            LogosLibraryInitializationWrapper_Initialize(s_debugBreakDelegate);
            Console.Error.WriteLine("[*] Logos library initialized.");

            Console.Error.WriteLine("[*] Loading license manager...");
            IntPtr licMgr = LicenseManagerCore_New(userId, licenseFolder);
            if (licMgr == IntPtr.Zero)
            {
                Console.Error.WriteLine("[!] Failed to create license manager.");
                return;
            }
            LicenseManagerCore_LoadCore(licMgr);
            Console.Error.WriteLine("[*] License manager loaded.");

            IntPtr title = OpenResource(licMgr, resourceFile);
            if (title == IntPtr.Zero)
            {
                LicenseManagerCore_Delete(licMgr);
                return;
            }

            ExecuteOperation(title, mode, articleNum, maxChars, findPattern);

            // Cleanup
            LogosLibraryInitializationWrapper_Uninitialize();
            LicenseManagerCore_Delete(licMgr);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[!] Error: {ex.GetType().Name}: {ex.Message}");
            Console.Error.WriteLine(ex.StackTrace);
        }
    }

    static IntPtr OpenResource(IntPtr licMgr, string resourceFile)
    {
        if (SinaiInterop_TryGetResourceIdAndVersion(licMgr, resourceFile, out string resId, out string resVer))
        {
            Console.Error.WriteLine($"[*] Resource: {resId} v{resVer}");
        }

        Console.Error.WriteLine($"[*] Opening: {System.IO.Path.GetFileName(resourceFile)}");
        IntPtr title = SinaiInterop_LoadTitleWithoutDataTypeOptions(
            licMgr,
            IntPtr.Zero,
            resourceFile,
            IntPtr.Zero,
            "2025-05-27T00:00:00Z",  // latest driver version
            "10.0.0",                 // latest data types version
            TitleLoadHint.Normal,
            out TitleLoadResult loadResult);

        Console.Error.WriteLine($"[*] Load result: {loadResult}");

        if (loadResult != TitleLoadResult.Success || title == IntPtr.Zero)
        {
            Console.Error.WriteLine($"[!] Failed to open resource. Result: {loadResult}");
            if (loadResult == TitleLoadResult.Locked)
                Console.Error.WriteLine("[!] Resource is locked (not licensed).");
            return IntPtr.Zero;
        }

        string titleResId = SinaiInterop_CTitle_GetResourceId(title);
        string titleResVer = SinaiInterop_CTitle_GetResourceVersion(title);
        string titleDriverVer = SinaiInterop_CTitle_GetResourceDriverVersion(title);
        Console.Error.WriteLine($"[*] Opened: {titleResId} v{titleResVer} (driver: {titleDriverVer})");
        return title;
    }

    static void ExecuteOperation(IntPtr title, string mode, int articleNum, int maxChars, string? findPattern)
    {
        switch (mode)
        {
            case "info":
                string infoResId = SinaiInterop_CTitle_GetResourceId(title);
                string infoResVer = SinaiInterop_CTitle_GetResourceVersion(title);
                string infoDriverVer = SinaiInterop_CTitle_GetResourceDriverVersion(title);
                Console.WriteLine($"ResourceId: {infoResId}");
                Console.WriteLine($"Version: {infoResVer}");
                Console.WriteLine($"DriverVersion: {infoDriverVer}");
                int count = 0;
                for (int i = 0; i < 200000; i++)
                {
                    if (!SinaiInterop_CTitle_IsArticle(title, i))
                        break;
                    count++;
                }
                Console.WriteLine($"ArticleCount: {count}");
                try
                {
                    Console.WriteLine($"IsBible: {CTitle_IsBible(title)}");
                    Console.WriteLine($"HasInterlinear: {CTitle_HasInterlinear(title)}");
                    Console.WriteLine($"HasReverseInterlinear: {CTitle_HasReverseInterlinear(title)}");
                    if (CTitle_HasInterlinear(title))
                    {
                        IntPtr intData = CTitle_GetInterlinearData(title);
                        if (intData != IntPtr.Zero)
                        {
                            int lineCount = CInterlinearData_GetLineCount(intData);
                            Console.WriteLine($"InterlinearLineCount: {lineCount}");
                            for (int il = 0; il < lineCount; il++)
                            {
                                IntPtr line = CInterlinearData_GetLine(intData, il);
                                if (line != IntPtr.Zero)
                                {
                                    string label = SinaiInterop_Interlinear_GetLabel(line);
                                    bool showDefault = SinaiInterop_Interlinear_GetShowDefault(line);
                                    Console.WriteLine($"InterlinearLine[{il}]: {label ?? "(null)"} (default={showDefault})");
                                }
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[!] Interlinear info error: {ex.Message}");
                }
                break;

            case "list":
                Console.WriteLine("Article#\tArticleId");
                for (int i = 0; i < 200000; i++)
                {
                    if (!SinaiInterop_CTitle_IsArticle(title, i))
                        break;
                    SinaiInterop_CTitle_ArticleNumberToArticleId(title, i, out string artId);
                    Console.WriteLine($"{i}\t{artId ?? "(null)"}");
                }
                break;

            case "toc":
                int tocRoot = SinaiInterop_CTitle_GetTOCRoot(title);
                Console.Error.WriteLine($"[*] TOC root entry: {tocRoot}");
                PrintTOC(title, tocRoot, 0);
                break;

            case "find-article":
                if (findPattern == null)
                {
                    Console.Error.WriteLine("[!] No search pattern provided.");
                    break;
                }
                string lowerPattern = findPattern.ToLowerInvariant();
                Console.WriteLine("Article#\tArticleId");
                for (int i = 0; i < 200000; i++)
                {
                    if (!SinaiInterop_CTitle_IsArticle(title, i))
                        break;
                    SinaiInterop_CTitle_ArticleNumberToArticleId(title, i, out string fArtId);
                    if (fArtId != null && fArtId.ToLowerInvariant().Contains(lowerPattern))
                    {
                        Console.WriteLine($"{i}\t{fArtId}");
                    }
                }
                break;

            case "read":
                if (!SinaiInterop_CTitle_IsArticle(title, articleNum))
                {
                    Console.Error.WriteLine($"[!] Article {articleNum} does not exist.");
                    break;
                }

                SinaiInterop_CTitle_ArticleNumberToArticleId(title, articleNum, out string readArtId);
                Console.Error.WriteLine($"[*] Reading article {articleNum} (id: {readArtId})");

                int absStart = SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(title, articleNum, false);
                int absEnd = SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(title, articleNum, true);
                Console.Error.WriteLine($"[*] Article offset range: {absStart} - {absEnd} ({absEnd - absStart} chars)");

                int length = Math.Min(absEnd - absStart, maxChars);
                if (length <= 0) length = maxChars;

                if (SinaiInterop_CTitle_GetExactText(title, articleNum, 0, length, out string text))
                {
                    Console.WriteLine(text);
                }
                else
                {
                    Console.Error.WriteLine("[!] GetExactText returned false.");
                }
                break;

            case "interlinear":
                ExecuteInterlinear(title, articleNum);
                break;

            case "navindex":
                IntPtr navResource = CTitle_GetResource(title);
                IntPtr resVol = SinaiInterop_ResourceVolumeFromResource(navResource);
                if (resVol == IntPtr.Zero)
                {
                    Console.Error.WriteLine("[!] Could not get ResourceVolume");
                    break;
                }
                Console.Error.WriteLine("[*] Exporting navigation index...");

                // Build article offset lookup table: absolute_offset -> article_num
                var articleOffsets = new List<(int articleNum, int absOffset)>();
                for (int ai = 0; ai < 200000; ai++)
                {
                    if (!SinaiInterop_CTitle_IsArticle(title, ai))
                        break;
                    int absOff = SinaiInterop_CTitle_GetAbsoluteCharacterOffsetForArticle(title, ai, false);
                    articleOffsets.Add((ai, absOff));
                }
                Console.Error.WriteLine($"[*] Built offset table for {articleOffsets.Count} articles");

                // Raw navindex entries: (ref, absStart, length)
                var navRawEntries = new List<(string refStr, uint absStart, uint length)>();
                var navTopicEntries = new List<string>();

                NavIndexReferenceCallback refCb = (IntPtr reference, uint absStart, uint length) =>
                {
                    string refStr = Marshal.PtrToStringUni(reference) ?? "";
                    navRawEntries.Add((refStr, absStart, length));
                    return true;
                };
                NavIndexTopicCallback topicCb = (IntPtr key, IntPtr name, uint absStart, uint length) =>
                {
                    string keyStr = Marshal.PtrToStringUni(key) ?? "";
                    string nameStr = Marshal.PtrToStringUni(name) ?? "";
                    navTopicEntries.Add($"TOPIC\t{keyStr}\t{nameStr}\t{absStart}\t{length}");
                    return true;
                };

                var refCbHandle = GCHandle.Alloc(refCb);
                var topicCbHandle = GCHandle.Alloc(topicCb);
                try
                {
                    IntPtr visitor = ManagedNavigationIndexVisitor_New(
                        Marshal.GetFunctionPointerForDelegate(refCb),
                        Marshal.GetFunctionPointerForDelegate(topicCb));

                    if (visitor != IntPtr.Zero)
                    {
                        SinaiInterop_ExportNavigationIndex(title, resVol, visitor);
                        ManagedNavigationIndexVisitor_Delete(visitor);
                    }
                    else
                    {
                        Console.Error.WriteLine("[!] Failed to create navigation index visitor");
                    }
                }
                finally
                {
                    refCbHandle.Free();
                    topicCbHandle.Free();
                }

                // Resolve absolute offsets to article numbers via binary search
                foreach (var rawEntry in navRawEntries)
                {
                    int artNum = -1;
                    int artOffset = 0;
                    // Binary search: find last article whose absOffset <= rawEntry.absStart
                    int lo = 0, hi = articleOffsets.Count - 1;
                    while (lo <= hi)
                    {
                        int mid = (lo + hi) / 2;
                        if (articleOffsets[mid].absOffset <= (int)rawEntry.absStart)
                        {
                            artNum = articleOffsets[mid].articleNum;
                            artOffset = (int)rawEntry.absStart - articleOffsets[mid].absOffset;
                            lo = mid + 1;
                        }
                        else
                        {
                            hi = mid - 1;
                        }
                    }
                    Console.WriteLine($"REF\t{rawEntry.refStr}\t{artNum}\t{artOffset}");
                }
                foreach (var entry in navTopicEntries)
                    Console.WriteLine(entry);
                Console.Error.WriteLine($"[*] Navigation index: {navRawEntries.Count} references, {navTopicEntries.Count} topics");
                break;

            case "article-title":
                IntPtr artResource = CTitle_GetResource(title);
                IntPtr artResVol = SinaiInterop_ResourceVolumeFromResource(artResource);
                if (artResVol != IntPtr.Zero)
                {
                    SinaiInterop_GetArticleTitle(title, artResVol, (uint)articleNum, out string artTitle);
                    Console.WriteLine(artTitle ?? "(no title)");
                }
                else
                {
                    Console.Error.WriteLine("[!] Could not get ResourceVolume");
                }
                break;
        }
    }

    // Thread-local storage for interlinear extraction results
    [ThreadStatic] static List<InterlinearWordEntry>? s_interlinearWords;
    [ThreadStatic] static List<string>? s_interlinearLineNames;

    struct InterlinearWordEntry
    {
        public string Word;
        public string[]? ColumnValues;
    }

    static void ExecuteInterlinear(IntPtr title, int articleNum)
    {
        // Step 1: Check if this resource has interlinear data
        bool hasInterlinear = false;
        try { hasInterlinear = CTitle_HasInterlinear(title); } catch { }

        bool hasReverseInterlinear = false;
        try { hasReverseInterlinear = CTitle_HasReverseInterlinear(title); } catch { }

        if (!hasInterlinear && !hasReverseInterlinear)
        {
            Console.Error.WriteLine("[!] This resource does not have interlinear data.");
            return;
        }

        if (!SinaiInterop_CTitle_IsArticle(title, articleNum))
        {
            Console.Error.WriteLine($"[!] Article {articleNum} does not exist.");
            return;
        }

        SinaiInterop_CTitle_ArticleNumberToArticleId(title, articleNum, out string artId);
        Console.Error.WriteLine($"[*] Extracting interlinear data for article {articleNum} (id: {artId})");
        Console.Error.WriteLine($"[*] HasInterlinear: {hasInterlinear}, HasReverseInterlinear: {hasReverseInterlinear}");

        // Step 2: Get interlinear line definitions
        var lineNames = new List<string>();
        IntPtr intData = IntPtr.Zero;
        try
        {
            intData = CTitle_GetInterlinearData(title);
            if (intData != IntPtr.Zero)
            {
                int lineCount = CInterlinearData_GetLineCount(intData);
                Console.Error.WriteLine($"[*] Interlinear lines: {lineCount}");
                for (int i = 0; i < lineCount; i++)
                {
                    IntPtr line = CInterlinearData_GetLine(intData, i);
                    if (line != IntPtr.Zero)
                    {
                        string label = SinaiInterop_Interlinear_GetLabel(line);
                        lineNames.Add(label ?? $"Line{i}");
                        bool showDefault = SinaiInterop_Interlinear_GetShowDefault(line);
                        Console.Error.WriteLine($"[*]   Line[{i}]: {label} (default={showDefault})");
                    }
                    else
                    {
                        lineNames.Add($"Line{i}");
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[!] Error getting interlinear line definitions: {ex.Message}");
        }

        // Step 3: Use NativeLogosResourceIndexer to extract word-by-word interlinear data
        s_interlinearWords = new List<InterlinearWordEntry>();
        s_interlinearLineNames = lineNames;

        // Keep delegates alive for the duration of the callback
        AddDefaultSectionStartCallback addDefaultSectionStart = OnAddDefaultSectionStart;
        AddNamedSectionCallback addNamedSectionStart = OnAddNamedSectionStart;
        AddNamedSectionCallback addNamedSectionEnd = OnAddNamedSectionEnd;
        AddMediaCallback addMedia = OnAddMedia;
        AddWordCallback addWord = OnAddWord;
        AddReferenceCallback addReference = OnAddReference;
        AddWordCallback addResourceJump = OnAddResourceJump;
        ProcessReverseInterlinearIndexDataCallback processRvi = OnProcessReverseInterlinearIndexData;
        SetLanguageCallback setLanguage = OnSetLanguage;

        // Pin the delegates to prevent GC
        var pins = new GCHandle[]
        {
            GCHandle.Alloc(addDefaultSectionStart),
            GCHandle.Alloc(addNamedSectionStart),
            GCHandle.Alloc(addNamedSectionEnd),
            GCHandle.Alloc(addMedia),
            GCHandle.Alloc(addWord),
            GCHandle.Alloc(addReference),
            GCHandle.Alloc(addResourceJump),
            GCHandle.Alloc(processRvi),
            GCHandle.Alloc(setLanguage),
        };

        try
        {
            // Constructor takes 9 function pointers (derived from mangled C++ symbol):
            // 1=AddDefaultSectionStart, 2=AddNamedSectionStart, 3=AddNamedSectionEnd,
            // 4=AddMedia, 5=AddReference(13params), 6=AddWord(11params),
            // 7=AddResourceJump(=AddWord), 8=ProcessRVI, 9=SetLanguage
            IntPtr callbackImpl = NativeLogosResourceIndexerCallbackImpl_New(
                Marshal.GetFunctionPointerForDelegate(addDefaultSectionStart),
                Marshal.GetFunctionPointerForDelegate(addNamedSectionStart),
                Marshal.GetFunctionPointerForDelegate(addNamedSectionEnd),
                Marshal.GetFunctionPointerForDelegate(addMedia),
                Marshal.GetFunctionPointerForDelegate(addReference),
                Marshal.GetFunctionPointerForDelegate(addWord),
                Marshal.GetFunctionPointerForDelegate(addResourceJump),
                Marshal.GetFunctionPointerForDelegate(processRvi),
                Marshal.GetFunctionPointerForDelegate(setLanguage)
            );

            if (callbackImpl == IntPtr.Zero)
            {
                Console.Error.WriteLine("[!] Failed to create indexer callback.");
                return;
            }

            Console.Error.WriteLine($"[*] Created indexer callback: {callbackImpl}");

            IntPtr indexer = NativeLogosResourceIndexer_New(title, callbackImpl);
            if (indexer == IntPtr.Zero)
            {
                Console.Error.WriteLine("[!] Failed to create indexer.");
                NativeLogosResourceIndexerCallbackImpl_Delete(callbackImpl);
                return;
            }

            Console.Error.WriteLine($"[*] Created indexer: {indexer}");
            Console.Error.WriteLine($"[*] Indexing article {articleNum}...");

            NativeLogosResourceIndexer_IndexArticle(indexer, articleNum);
            NativeLogosResourceIndexer_FinishIndexing(indexer);

            Console.Error.WriteLine($"[*] Indexing complete. Words collected: {s_interlinearWords.Count}");

            // Step 4: Output the results
            // Determine how many columns we have from the RVI data
            int maxCols = 0;
            foreach (var word in s_interlinearWords)
            {
                if (word.ColumnValues != null && word.ColumnValues.Length > maxCols)
                    maxCols = word.ColumnValues.Length;
            }

            // Build header: use lineNames if available, otherwise generic Column# names
            var header = new StringBuilder();
            header.Append("Word");
            if (maxCols > 0)
            {
                for (int c = 0; c < maxCols; c++)
                {
                    header.Append('\t');
                    header.Append(c < lineNames.Count ? lineNames[c] : $"Column{c}");
                }
            }
            else if (lineNames.Count > 0)
            {
                // No RVI data received, just show line names as header
                foreach (string ln in lineNames)
                {
                    header.Append('\t');
                    header.Append(ln);
                }
            }
            Console.WriteLine(header.ToString());

            // Output each word
            foreach (var word in s_interlinearWords)
            {
                var sb = new StringBuilder();
                sb.Append(word.Word ?? "");
                if (word.ColumnValues != null)
                {
                    for (int c = 0; c < maxCols; c++)
                    {
                        sb.Append('\t');
                        sb.Append(c < word.ColumnValues.Length ? word.ColumnValues[c] ?? "" : "");
                    }
                }
                Console.WriteLine(sb.ToString());
            }

            // Cleanup
            NativeLogosResourceIndexer_Delete(indexer);
            NativeLogosResourceIndexerCallbackImpl_Delete(callbackImpl);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[!] Indexer error: {ex.GetType().Name}: {ex.Message}");
            Console.Error.WriteLine(ex.StackTrace);
        }
        finally
        {
            foreach (var pin in pins)
                pin.Free();
            s_interlinearWords = null;
            s_interlinearLineNames = null;
        }
    }

    // Indexer callback implementations
    // All use IntPtr for string params to avoid marshalling issues; we marshal manually
    static void OnAddDefaultSectionStart(int offset)
    {
        // No-op for interlinear extraction
    }

    static void OnAddNamedSectionStart(IntPtr name, int offset)
    {
        // No-op
    }

    static void OnAddNamedSectionEnd(IntPtr name, int offset)
    {
        // No-op
    }

    static void OnAddMedia(int mediaType, int a, int b, int c, int d, IntPtr data, int e, int f, int g, int h)
    {
        // No-op
    }

    // AddWord: 11 params
    static void OnAddWord(
        IntPtr wordPtr, int a, int b, int c, int d, int e,
        IntPtr word2Ptr, int f, int g, int h, int i2)
    {
        if (s_interlinearWords == null) return;
        try
        {
            string? word = wordPtr != IntPtr.Zero ? Marshal.PtrToStringUni(wordPtr) : null;
            if (!string.IsNullOrEmpty(word))
            {
                s_interlinearWords.Add(new InterlinearWordEntry { Word = word, ColumnValues = null });
            }
        }
        catch { }
    }

    // AddReference: 13 params
    static void OnAddReference(
        IntPtr ref1, int offset,
        IntPtr ref2, int a, int b, int c, int d, int e,
        IntPtr ref3, int f, int g, int h, int i2)
    {
        // No-op
    }

    // AddResourceJump: 11 params (same as AddWord)
    static void OnAddResourceJump(
        IntPtr refPtr, int a, int b, int c, int d, int e,
        IntPtr ref2Ptr, int f, int g, int h, int i2)
    {
        // No-op
    }

    // ProcessReverseInterlinearIndexData: (char16_t const*, ReverseInterlinearColumnIndexData const*, int)
    static void OnProcessReverseInterlinearIndexData(
        IntPtr wordPtr, IntPtr columnData, int columnCount)
    {
        if (s_interlinearWords == null) return;

        string? word = null;
        try { word = wordPtr != IntPtr.Zero ? Marshal.PtrToStringUni(wordPtr) : null; } catch { }

        // ReverseInterlinearColumnIndexData is a struct array at columnData
        // Each struct likely contains a string pointer (char16_t*) as the first field
        // Try reading as array of pointers to strings
        string[]? values = null;
        if (columnData != IntPtr.Zero && columnCount > 0)
        {
            values = new string[columnCount];
            int ptrSize = IntPtr.Size;
            for (int i = 0; i < columnCount; i++)
            {
                try
                {
                    // Try reading each entry as a pointer to a char16_t string
                    IntPtr strPtr = Marshal.ReadIntPtr(columnData, i * ptrSize);
                    if (strPtr != IntPtr.Zero)
                    {
                        values[i] = Marshal.PtrToStringUni(strPtr) ?? "";
                    }
                    else
                    {
                        values[i] = "";
                    }
                }
                catch
                {
                    values[i] = "?";
                }
            }
        }

        s_interlinearWords.Add(new InterlinearWordEntry
        {
            Word = word ?? "",
            ColumnValues = values
        });
    }

    static void OnSetLanguage(IntPtr languagePtr)
    {
        try
        {
            string? language = languagePtr != IntPtr.Zero ? Marshal.PtrToStringUni(languagePtr) : null;
            Console.Error.WriteLine($"[*] Language: {language ?? "(null)"}");
        }
        catch { }
    }

    static void RunBatchMode(string resourcesBase, string userId, string licenseFolder)
    {
        Console.Error.WriteLine("[*] Batch mode: Initializing Logos native library...");

        try
        {
            LogosLibraryInitializationWrapper_Initialize(s_debugBreakDelegate);
            Console.Error.WriteLine("[*] Logos library initialized.");

            Console.Error.WriteLine("[*] Loading license manager...");
            IntPtr licMgr = LicenseManagerCore_New(userId, licenseFolder);
            if (licMgr == IntPtr.Zero)
            {
                Console.Error.WriteLine("[!] Failed to create license manager.");
                return;
            }
            LicenseManagerCore_LoadCore(licMgr);
            Console.Error.WriteLine("[*] License manager loaded.");

            // Cache of opened resources: filepath -> title pointer
            var resourceCache = new Dictionary<string, IntPtr>();
            var volumeCache = new Dictionary<string, IntPtr>();
            var volumeDbCache = new Dictionary<string, IntPtr>();

            Console.Error.WriteLine("[*] Batch mode ready. Reading commands from stdin...");

            string line;
            while ((line = Console.ReadLine()) != null)
            {
                line = line.Trim();
                if (line.Length == 0)
                    break;

                try
                {
                    // Parse command line into tokens (respecting quoted strings)
                    var tokens = ParseCommandLine(line);
                    if (tokens.Count == 0)
                    {
                        Console.WriteLine("---END---");
                        continue;
                    }

                    string cmd = tokens[0].ToLowerInvariant();
                    string mode;
                    string resourceFile;
                    int articleNum = 0;
                    int maxChars = 10000;
                    string findPattern = null;

                    switch (cmd)
                    {
                        case "read":
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] read requires: read <file> <article#> <max-chars>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "read";
                            resourceFile = tokens[1];
                            if (tokens.Count >= 3) int.TryParse(tokens[2], out articleNum);
                            if (tokens.Count >= 4) int.TryParse(tokens[3], out maxChars);
                            break;

                        case "list":
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] list requires: list <file>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "list";
                            resourceFile = tokens[1];
                            break;

                        case "info":
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] info requires: info <file>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "info";
                            resourceFile = tokens[1];
                            break;

                        case "toc":
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] toc requires: toc <file>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "toc";
                            resourceFile = tokens[1];
                            break;

                        case "find-article":
                            if (tokens.Count < 3)
                            {
                                Console.Error.WriteLine("[!] find-article requires: find-article <file> <pattern>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "find-article";
                            resourceFile = tokens[1];
                            findPattern = tokens[2];
                            break;

                        case "interlinear":
                            if (tokens.Count < 3)
                            {
                                Console.Error.WriteLine("[!] interlinear requires: interlinear <file> <article#>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "interlinear";
                            resourceFile = tokens[1];
                            if (tokens.Count >= 3) int.TryParse(tokens[2], out articleNum);
                            break;

                        case "navindex":
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] navindex requires: navindex <file>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "navindex";
                            resourceFile = tokens[1];
                            break;

                        case "article-title":
                            if (tokens.Count < 3)
                            {
                                Console.Error.WriteLine("[!] article-title requires: article-title <file> <article#>");
                                Console.WriteLine("---END---");
                                continue;
                            }
                            mode = "article-title";
                            resourceFile = tokens[1];
                            int.TryParse(tokens[2], out articleNum);
                            break;

                        case "query-db":
                        {
                            if (tokens.Count < 4)
                            {
                                Console.Error.WriteLine("[!] query-db requires: query-db <file> <db-name> <sql>");
                                mode = "__skip__";
                                resourceFile = "";
                                break;
                            }
                            string volFile = tokens[1];
                            string dbName = tokens[2];
                            string sql = tokens[3];

                            if (!volFile.Contains("/"))
                                volFile = $"{resourcesBase}/{volFile}";

                            string cacheKey = volFile + "|" + dbName;
                            IntPtr dbHandle;
                            if (!volumeDbCache.TryGetValue(cacheKey, out dbHandle))
                            {
                                IntPtr volHandle;
                                if (!volumeCache.TryGetValue(volFile, out volHandle))
                                {
                                    volHandle = EncryptedVolume_New();
                                    bool opened = EncryptedVolume_Open(volHandle, licMgr, volFile);
                                    if (!opened)
                                    {
                                        Console.Error.WriteLine($"[!] Failed to open volume: {volFile}");
                                        mode = "__skip__";
                                        resourceFile = "";
                                        break;
                                    }
                                    volumeCache[volFile] = volHandle;
                                }
                                dbHandle = EncryptedVolume_OpenDatabase(volHandle, dbName);
                                if (dbHandle == IntPtr.Zero)
                                {
                                    Console.Error.WriteLine($"[!] Failed to open DB {dbName} in {volFile}");
                                    mode = "__skip__";
                                    resourceFile = "";
                                    break;
                                }
                                volumeDbCache[cacheKey] = dbHandle;
                            }

                            byte[] sqlBytes = System.Text.Encoding.UTF8.GetBytes(sql + "\0");
                            int rc = sqlite3_prepare_v2(dbHandle, sqlBytes, -1, out IntPtr stmt, out IntPtr tail);
                            if (rc != SQLITE_OK)
                            {
                                IntPtr errMsg = sqlite3_errmsg(dbHandle);
                                string err = Marshal.PtrToStringUTF8(errMsg) ?? "unknown error";
                                Console.Error.WriteLine($"[!] SQL error: {err}");
                                mode = "__skip__";
                                resourceFile = "";
                                break;
                            }

                            int colCount = sqlite3_column_count(stmt);
                            var colNames = new string[colCount];
                            for (int ci = 0; ci < colCount; ci++)
                            {
                                IntPtr namePtr = sqlite3_column_name(stmt, ci);
                                colNames[ci] = Marshal.PtrToStringUTF8(namePtr) ?? $"col{ci}";
                            }
                            Console.WriteLine(string.Join("\t", colNames));

                            int rowCount = 0;
                            while (sqlite3_step(stmt) == SQLITE_ROW && rowCount < 500000)
                            {
                                var vals = new string[colCount];
                                for (int ci = 0; ci < colCount; ci++)
                                {
                                    if (sqlite3_column_type(stmt, ci) == SQLITE_NULL)
                                        vals[ci] = "";
                                    else
                                    {
                                        IntPtr textPtr = sqlite3_column_text(stmt, ci);
                                        vals[ci] = Marshal.PtrToStringUTF8(textPtr) ?? "";
                                    }
                                }
                                Console.WriteLine(string.Join("\t", vals));
                                rowCount++;
                            }
                            sqlite3_finalize(stmt);

                            mode = "__skip__";
                            resourceFile = "";
                            break;
                        }

                        case "volume-info":
                        {
                            if (tokens.Count < 2)
                            {
                                Console.Error.WriteLine("[!] volume-info requires: volume-info <file>");
                                mode = "__skip__";
                                resourceFile = "";
                                break;
                            }
                            string volFile = tokens[1];
                            if (!volFile.Contains("/"))
                                volFile = $"{resourcesBase}/{volFile}";

                            IntPtr volHandle;
                            if (!volumeCache.TryGetValue(volFile, out volHandle))
                            {
                                volHandle = EncryptedVolume_New();
                                bool opened = EncryptedVolume_Open(volHandle, licMgr, volFile);
                                if (!opened)
                                {
                                    Console.Error.WriteLine($"[!] Failed to open volume: {volFile}");
                                    mode = "__skip__";
                                    resourceFile = "";
                                    break;
                                }
                                volumeCache[volFile] = volHandle;
                            }

                            string resId = EncryptedVolume_GetResourceId(volHandle) ?? "unknown";
                            string driverName = EncryptedVolume_GetResourceDriverName(volHandle) ?? "unknown";
                            Console.WriteLine($"ResourceId: {resId}");
                            Console.WriteLine($"DriverName: {driverName}");

                            mode = "__skip__";
                            resourceFile = "";
                            break;
                        }

                        default:
                            Console.Error.WriteLine($"[!] Unknown command: {cmd}");
                            Console.WriteLine("---END---");
                            continue;
                    }

                    // Skip CTitle path for EncryptedVolume commands
                    if (mode == "__skip__")
                        goto printEnd;

                    // Resolve resource path
                    if (!resourceFile.Contains("/"))
                        resourceFile = $"{resourcesBase}/{resourceFile}";

                    // Get or open resource (cached)
                    if (!resourceCache.TryGetValue(resourceFile, out IntPtr title))
                    {
                        title = OpenResource(licMgr, resourceFile);
                        if (title == IntPtr.Zero)
                        {
                            Console.Error.WriteLine($"[!] Failed to open: {resourceFile}");
                            Console.WriteLine("---END---");
                            continue;
                        }
                        resourceCache[resourceFile] = title;
                    }

                    ExecuteOperation(title, mode, articleNum, maxChars, findPattern);
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"[!] Command error: {ex.GetType().Name}: {ex.Message}");
                }

                printEnd:
                Console.WriteLine("---END---");
                Console.Out.Flush();
            }

            Console.Error.WriteLine("[*] Batch mode: shutting down...");

            // Cleanup
            LogosLibraryInitializationWrapper_Uninitialize();
            LicenseManagerCore_Delete(licMgr);
            Console.Error.WriteLine("[*] Batch mode: done.");
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[!] Batch error: {ex.GetType().Name}: {ex.Message}");
            Console.Error.WriteLine(ex.StackTrace);
        }
    }

    /// <summary>
    /// Parse a command line string into tokens, respecting double-quoted strings.
    /// </summary>
    static List<string> ParseCommandLine(string line)
    {
        var tokens = new List<string>();
        int i = 0;
        while (i < line.Length)
        {
            // Skip whitespace
            while (i < line.Length && char.IsWhiteSpace(line[i]))
                i++;
            if (i >= line.Length)
                break;

            if (line[i] == '"')
            {
                // Quoted token
                i++; // skip opening quote
                int start = i;
                while (i < line.Length && line[i] != '"')
                    i++;
                tokens.Add(line.Substring(start, i - start));
                if (i < line.Length) i++; // skip closing quote
            }
            else
            {
                // Unquoted token
                int start = i;
                while (i < line.Length && !char.IsWhiteSpace(line[i]))
                    i++;
                tokens.Add(line.Substring(start, i - start));
            }
        }
        return tokens;
    }

    static void PrintTOC(IntPtr title, int entry, int depth)
    {
        SinaiInterop_CTitle_GetTOCEntryLabel(title, entry, out string label);
        SinaiInterop_CTitle_GetTOCLocation(title, entry, out int article, out int offset);

        string indent = new string(' ', depth * 2);
        Console.WriteLine($"{indent}{label ?? "(root)"} [article={article}, offset={offset}]");

        IntPtr childrenPtr = SinaiInterop_CTitle_GetTOCEntryChildren(title, entry);
        if (childrenPtr != IntPtr.Zero)
        {
            try
            {
                // MarshalArrayInt32: first int is count, then int[] values
                int count = Marshal.ReadInt32(childrenPtr);
                for (int i = 0; i < count && i < 1000; i++)
                {
                    int childEntry = Marshal.ReadInt32(childrenPtr, 4 + i * 4);
                    PrintTOC(title, childEntry, depth + 1);
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"[!] TOC children error: {ex.Message}");
            }
        }
    }
}
