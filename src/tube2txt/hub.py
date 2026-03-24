import os
import sqlite3
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional

# For pip-installed packages, the database and projects dir should be relative to CWD
# unless specified via environment variables.
CWD = os.getcwd()
DB_PATH = os.environ.get("TUBE2TXT_DB", os.path.join(CWD, "tube2txt.db"))
PROJECTS_DIR = os.path.join(CWD, "projects")

app = FastAPI(title="Tube2Txt Hub")

# Database helper
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Serve projects directory
if os.path.exists(PROJECTS_DIR):
    app.mount("/projects", StaticFiles(directory=PROJECTS_DIR), name="projects")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tube2Txt Hub</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen" x-data="hub()">
    <nav class="bg-indigo-600 text-white p-4 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold">Tube2Txt Hub</h1>
            <div class="relative w-1/3">
                <input 
                    type="text" 
                    x-model="searchQuery" 
                    @input.debounce.300ms="search()"
                    placeholder="Search all transcripts..." 
                    class="w-full p-2 pl-10 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                <svg class="w-5 h-5 absolute left-3 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
            </div>
        </div>
    </nav>

    <main class="container mx-auto p-6">
        <!-- Search Results -->
        <template x-if="searchResults.length > 0">
            <section class="mb-12">
                <h2 class="text-xl font-semibold mb-4 text-gray-700">Search Results</h2>
                <div class="bg-white rounded-xl shadow-md overflow-hidden">
                    <ul class="divide-y divide-gray-200">
                        <template x-for="result in searchResults" :key="result.id">
                            <li class="p-4 hover:bg-gray-50 cursor-pointer" @click="openVideo(result.slug, result.start_ts)">
                                <div class="flex items-center space-x-4">
                                    <img :src="'/projects/' + result.slug + '/' + result.thumbnail_path" class="w-24 h-16 object-cover rounded shadow">
                                    <div>
                                        <p class="font-medium text-indigo-600" x-text="result.title"></p>
                                        <p class="text-sm text-gray-500" x-text="'[' + result.start_ts + '] ' + result.text"></p>
                                    </div>
                                </div>
                            </li>
                        </template>
                    </ul>
                </div>
            </section>
        </template>

        <!-- Video Gallery -->
        <section>
            <h2 class="text-xl font-semibold mb-6 text-gray-700">Your Video Library</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                <template x-for="video in videos" :key="video.id">
                    <div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow cursor-pointer" @click="openVideo(video.slug)">
                        <div class="h-48 bg-gray-200 relative">
                            <!-- Placeholder for latest thumbnail -->
                            <div class="absolute inset-0 flex items-center justify-center text-gray-400">
                                <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                            </div>
                        </div>
                        <div class="p-4">
                            <h3 class="font-bold text-gray-800 truncate" x-text="video.title"></h3>
                            <p class="text-xs text-gray-500 mt-1" x-text="'Processed: ' + new Date(video.processed_at).toLocaleDateString()"></p>
                        </div>
                    </div>
                </template>
            </div>
        </section>
    </main>

    <script>
        function hub() {
            return {
                videos: [],
                searchResults: [],
                searchQuery: '',
                async init() {
                    const res = await fetch('/api/videos');
                    this.videos = await res.json();
                },
                async search() {
                    if (this.searchQuery.length < 2) {
                        this.searchResults = [];
                        return;
                    }
                    const res = await fetch(`/api/search?q=${encodeURIComponent(this.searchQuery)}`);
                    this.searchResults = await res.json();
                },
                openVideo(slug, ts = '') {
                    window.open(`/projects/${slug}/index.html${ts ? '#' + ts : ''}`, '_blank');
                }
            }
        }
    </script>
</body>
</html>
    """

@app.get("/api/videos")
async def get_videos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos ORDER BY processed_at DESC")
    videos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return videos

@app.get("/api/search")
async def search(q: str = Query(...)):
    conn = get_db()
    cursor = conn.cursor()
    # Join with videos to get slug and title
    query = """
        SELECT s.*, v.slug, v.title
        FROM segments s
        JOIN videos v ON s.video_id = v.id
        WHERE s.id IN (
            SELECT segment_id FROM segments_search WHERE segments_search MATCH ?
        )
        LIMIT 20
    """
    cursor.execute(query, (q,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def start_hub():
    """Entry point for the hub command."""
    print(f"Starting Tube2Txt Hub at http://localhost:8000")
    print(f"Database: {DB_PATH}")
    print(f"Projects: {PROJECTS_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_hub()
