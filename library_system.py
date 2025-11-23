import threading
import webbrowser
from datetime import datetime, timedelta
from typing import List, Optional

from flask import Flask, jsonify, request, Response

app = Flask(__name__)

# -------------------- PYTHON BACKEND LOGIC --------------------

ISSUE_DAYS = 7
FINE_PER_DAY = 10


class Book:
    def __init__(self, id: int, title: str, author: str, year: int,
                 is_issued: bool = False, due_date: Optional[datetime] = None):
        self.id = id
        self.title = title
        self.author = author
        self.year = year
        self.is_issued = is_issued
        self.due_date = due_date

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "isIssued": self.is_issued,
            "dueDate": self.due_date.isoformat() if self.due_date else None,
        }


books_db: List[Book] = []


def init_books():
    global books_db
    now = datetime.now()
    books_db = [
        Book(101, "The C Programming Language", "Brian Kernighan", 1978),
        Book(102, "Clean Code", "Robert C. Martin", 2008),
        Book(103, "The Pragmatic Programmer", "Andrew Hunt", 1999,
             is_issued=True, due_date=now + timedelta(days=2)),
        Book(104, "Introduction to Algorithms", "Thomas H. Cormen", 2009),
        Book(105, "Design Patterns", "Erich Gamma", 1994),
        Book(106, "Harry Potter", "J.K. Rowling", 1997,
             is_issued=True, due_date=now - timedelta(days=2)),
        Book(107, "Dune", "Frank Herbert", 1965),
        Book(108, "1984", "George Orwell", 1949,
             is_issued=True, due_date=now + timedelta(days=3)),
        Book(109, "Sapiens", "Yuval Noah Harari", 2011),
        Book(110, "Atomic Habits", "James Clear", 2018),
        Book(111, "The Midnight Library", "Matt Haig", 2020,
             is_issued=True, due_date=now + timedelta(days=4)),
        Book(112, "Educated", "Tara Westover", 2018),
    ]


def find_book_index(book_id: int) -> int:
    for i, b in enumerate(books_db):
        if b.id == book_id:
            return i
    return -1


init_books()


# -------------------- API ENDPOINTS --------------------

@app.route("/api/books", methods=["GET"])
def get_books():
    return jsonify([b.to_dict() for b in books_db])


@app.route("/api/stats", methods=["GET"])
def get_stats():
    total = len(books_db)
    issued = len([b for b in books_db if b.is_issued])
    available = len([b for b in books_db if not b.is_issued])
    now = datetime.now()
    overdue = len([b for b in books_db
                   if b.is_issued and b.due_date is not None and now > b.due_date])
    return jsonify({
        "total": total,
        "issued": issued,
        "available": available,
        "overdue": overdue,
    })


@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.get_json(force=True)
    try:
        book_id = int(data.get("id"))
        title = str(data.get("title", "")).strip()
        author = str(data.get("author", "")).strip()
        year = int(data.get("year"))
    except Exception:
        return jsonify({"error": "Invalid data"}), 400

    if not title or not author:
        return jsonify({"error": "Title and author are required"}), 400

    if any(b.id == book_id for b in books_db):
        return jsonify({"error": "Book ID already exists"}), 400

    new_book = Book(book_id, title, author, year)
    books_db.append(new_book)
    return jsonify(new_book.to_dict())


@app.route("/api/books/<int:book_id>/issue", methods=["POST"])
def issue_book(book_id: int):
    idx = find_book_index(book_id)
    if idx == -1:
        return jsonify({"error": "Book not found"}), 404

    book = books_db[idx]
    if book.is_issued:
        return jsonify({"error": "Book already issued"}), 400

    book.is_issued = True
    book.due_date = datetime.now() + timedelta(days=ISSUE_DAYS)
    return jsonify(book.to_dict())


@app.route("/api/books/<int:book_id>/return", methods=["POST"])
def return_book(book_id: int):
    idx = find_book_index(book_id)
    if idx == -1:
        return jsonify({"error": "Book not found"}), 404

    book = books_db[idx]
    if not book.is_issued:
        return jsonify({"error": "Book is not issued"}), 400

    today = datetime.now()
    fine = 0
    days_overdue = 0

    if book.due_date and today > book.due_date:
        days_overdue = (today.date() - book.due_date.date()).days
        fine = days_overdue * FINE_PER_DAY

    # Update book state
    book.is_issued = False
    book.due_date = None

    return jsonify({
        "book": book.to_dict(),
        "fine": fine,
        "daysOverdue": days_overdue,
    })


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id: int):
    idx = find_book_index(book_id)
    if idx == -1:
        return jsonify({"error": "Book not found"}), 404
    del books_db[idx]
    return jsonify({"detail": "Book deleted"})


# -------------------- HTML + JS FRONTEND --------------------

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>LibraryHub - Python Library Management</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @keyframes blob {
      0%, 100% { transform: translate(0, 0) scale(1); }
      33% { transform: translate(30px, -50px) scale(1.1); }
      66% { transform: translate(-20px, 20px) scale(0.9); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideIn {
      from { transform: translateX(400px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    .animate-blob { animation: blob 7s infinite; }
    .animation-delay-2000 { animation-delay: 2s; }
    .animation-delay-4000 { animation-delay: 4s; }
    .animate-fadeIn { animation: fadeIn 0.4s ease-out; }
    .animate-slideIn { animation: slideIn 0.4s ease-out; }
    .scrollbar-hide::-webkit-scrollbar { display: none; }
  </style>
</head>
<body class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
  <!-- Animated Background -->
  <div class="fixed inset-0 overflow-hidden pointer-events-none">
    <div class="absolute top-20 right-10 w-96 h-96 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
    <div class="absolute bottom-20 left-10 w-96 h-96 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
    <div class="absolute top-1/2 left-1/2 w-96 h-96 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
  </div>

  <!-- Notification -->
  <div id="notification"
       class="hidden fixed top-6 right-6 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 animate-slideIn z-50">
    <span id="notification-icon" class="text-xl">ℹ️</span>
    <span id="notification-text" class="text-sm font-medium"></span>
  </div>

  <!-- Modal -->
  <div id="modal-backdrop"
       class="hidden fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-40 backdrop-blur-sm">
    <div class="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-700/50 animate-fadeIn"
         id="modal-card">
      <div class="bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 p-6 text-white">
        <h2 id="modal-title" class="text-2xl font-bold">Book Title</h2>
        <p id="modal-author" class="text-sm opacity-90 mt-2">Author</p>
      </div>
      <div class="p-6 space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-4 rounded-xl border border-slate-600/50">
            <p class="text-slate-400 text-xs font-semibold mb-1">ID</p>
            <p id="modal-id" class="font-bold text-lg text-cyan-400"></p>
          </div>
          <div class="bg-gradient-to-br from-slate-700/50 to-slate-800/50 p-4 rounded-xl border border-slate-600/50">
            <p class="text-slate-400 text-xs font-semibold mb-1">Year</p>
            <p id="modal-year" class="font-bold text-lg text-blue-400"></p>
          </div>
        </div>
        <div id="modal-status-box" class="p-4 rounded-xl border-2 bg-slate-800 border-slate-600">
          <p id="modal-status-text" class="font-bold text-lg text-slate-200">Status</p>
          <p id="modal-due" class="text-sm text-slate-300 mt-2"></p>
        </div>
        <div class="flex flex-col gap-3 pt-2">
          <button id="modal-issue-btn"
                  class="hidden w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-bold py-3 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
            📤 Issue Book
          </button>
          <button id="modal-return-btn"
                  class="hidden w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold py-3 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
            📥 Return Book
          </button>
          <button id="modal-delete-btn"
                  class="w-full bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white font-bold py-3 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
            🗑️ Delete
          </button>
          <button id="modal-close-btn"
                  class="w-full bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition-all duration-300 border border-slate-600">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="relative z-10">
    <!-- Header -->
    <header class="backdrop-blur-md bg-gradient-to-r from-slate-900/95 via-slate-800/95 to-slate-900/95 border-b border-cyan-500/20 sticky top-0 z-30 shadow-2xl">
      <div class="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
        <div class="flex items-center gap-4">
          <div class="p-3 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M4.5 5.25h15m-15 3.75h15m-15 3.75h15m-15 3.75h15" />
            </svg>
          </div>
          <div>
            <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
              LibraryHub
            </h1>
            <p class="text-xs text-slate-400">Modern Library Management • Python Backend</p>
          </div>
        </div>
      </div>
      <!-- Stats -->
      <div class="border-t border-slate-700/50 px-6 py-3 flex gap-6 overflow-x-auto scrollbar-hide max-w-7xl mx-auto">
        <div class="flex items-center gap-3 bg-gradient-to-r from-emerald-500/20 to-emerald-500/10 px-4 py-2 rounded-lg border border-emerald-500/30 whitespace-nowrap">
          <span class="text-emerald-400 text-lg">✅</span>
          <span class="text-sm text-slate-200">
            <span id="available-count" class="font-bold text-emerald-400">0</span> Available
          </span>
        </div>
        <div class="flex items-center gap-3 bg-gradient-to-r from-blue-500/20 to-blue-500/10 px-4 py-2 rounded-lg border border-blue-500/30 whitespace-nowrap">
          <span class="text-blue-400 text-lg">📕</span>
          <span class="text-sm text-slate-200">
            <span id="issued-count" class="font-bold text-blue-400">0</span> Issued
          </span>
        </div>
        <div class="flex items-center gap-3 bg-gradient-to-r from-red-500/20 to-red-500/10 px-4 py-2 rounded-lg border border-red-500/30 whitespace-nowrap">
          <span class="text-red-400 text-lg">⚠️</span>
          <span class="text-sm text-slate-200">
            <span id="overdue-count" class="font-bold text-red-400">0</span> Overdue
          </span>
        </div>
        <div class="flex items-center gap-3 bg-gradient-to-r from-slate-500/20 to-slate-500/10 px-4 py-2 rounded-lg border border-slate-500/30 whitespace-nowrap">
          <span class="text-slate-300 text-lg">📚</span>
          <span class="text-sm text-slate-200">
            <span id="total-count" class="font-bold text-slate-100">0</span> Total
          </span>
        </div>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="backdrop-blur-md bg-slate-800/60 border-b border-slate-700/50 sticky top-[92px] z-20">
      <div class="max-w-7xl mx-auto px-6 flex gap-3 py-3 overflow-x-auto scrollbar-hide">
        <button data-view="home"
                class="nav-btn px-6 py-2 rounded-xl font-bold border bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg border-cyan-400">
          📚 All Books
        </button>
        <button data-view="search"
                class="nav-btn px-6 py-2 rounded-xl font-bold border bg-slate-700/70 text-slate-300 border-slate-600 hover:bg-slate-600/80">
          🔍 Search
        </button>
        <button data-view="issued"
                class="nav-btn px-6 py-2 rounded-xl font-bold border bg-slate-700/70 text-slate-300 border-slate-600 hover:bg-slate-600/80">
          📤 Issued Books
        </button>
        <button data-view="issue"
                class="nav-btn px-6 py-2 rounded-xl font-bold border bg-slate-700/70 text-slate-300 border-slate-600 hover:bg-slate-600/80">
          ✅ Quick Issue
        </button>
        <button data-view="add"
                class="nav-btn px-6 py-2 rounded-xl font-bold border bg-slate-700/70 text-slate-300 border-slate-600 hover:bg-slate-600/80">
          ➕ Add Book
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8 min-h-[calc(100vh-200px)]">
      <div id="main-content" class="animate-fadeIn text-slate-200">
        <!-- Filled by JavaScript -->
      </div>
    </main>
  </div>

  <script>
    // ----------------- FRONTEND STATE -----------------
    let books = [];
    let currentView = "home";
    let selectedBook = null;
    const issueDays = 7;

    function showNotification(msg, type = "info") {
      const box = document.getElementById("notification");
      const text = document.getElementById("notification-text");
      const icon = document.getElementById("notification-icon");

      const baseClasses = "fixed top-6 right-6 px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 animate-slideIn z-50";
      let bg = "bg-blue-500";
      let iconChar = "ℹ️";

      if (type === "success") { bg = "bg-emerald-500"; iconChar = "✅"; }
      if (type === "error")   { bg = "bg-red-500";     iconChar = "❌"; }
      if (type === "warning") { bg = "bg-amber-500";   iconChar = "⚠️"; }

      box.className = baseClasses + " text-white " + bg;
      text.textContent = msg;
      icon.textContent = iconChar;
      box.classList.remove("hidden");

      setTimeout(() => {
        box.classList.add("hidden");
      }, 3000);
    }

    // --------------- STATUS UTILS ----------------------
    function getBookStatus(book) {
      if (!book.isIssued) {
        return {
          text: "Available",
          icon: "📗",
          color: "text-emerald-600",
          bg: "bg-emerald-100",
          border: "border-emerald-300"
        };
      }
      const today = new Date();
      const due = book.dueDate ? new Date(book.dueDate) : null;
      if (due && today > due) {
        return {
          text: "Overdue",
          icon: "⚠️",
          color: "text-red-600",
          bg: "bg-red-100",
          border: "border-red-300"
        };
      }
      return {
        text: "Issued",
        icon: "📕",
        color: "text-blue-600",
        bg: "bg-blue-100",
        border: "border-blue-300"
      };
    }

    function updateStatsBar() {
      fetch("/api/stats")
        .then(r => r.json())
        .then(stats => {
          document.getElementById("total-count").textContent = stats.total;
          document.getElementById("issued-count").textContent = stats.issued;
          document.getElementById("available-count").textContent = stats.available;
          document.getElementById("overdue-count").textContent = stats.overdue;
        })
        .catch(() => {});
    }

    // --------------- API CALLS -------------------------
    function loadBooks() {
      return fetch("/api/books")
        .then(r => r.json())
        .then(data => {
          books = data;
        });
    }

    function apiIssueBook(id) {
      return fetch(`/api/books/${id}/issue`, { method: "POST" })
        .then(r => r.json());
    }

    function apiReturnBook(id) {
      return fetch(`/api/books/${id}/return`, { method: "POST" })
        .then(r => r.json());
    }

    function apiDeleteBook(id) {
      return fetch(`/api/books/${id}`, { method: "DELETE" })
        .then(r => r.json());
    }

    function apiAddBook(payload) {
      return fetch("/api/books", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).then(r => r.json());
    }

    // --------------- RENDER FUNCTIONS ------------------
    function render() {
      const container = document.getElementById("main-content");
      if (currentView === "home") {
        renderHome(container);
      } else if (currentView === "search") {
        renderSearch(container);
      } else if (currentView === "issued") {
        renderIssued(container);
      } else if (currentView === "issue") {
        renderIssue(container);
      } else if (currentView === "add") {
        renderAdd(container);
      }
    }

    function renderHome(container) {
      let html = `
        <div class="mb-8">
          <h2 class="text-3xl font-bold text-white mb-1">All Books</h2>
          <p class="text-slate-400 text-sm">Click a book card to view details, issue, return, or delete.</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      `;

      if (books.length === 0) {
        html += `
          <div class="col-span-full text-center py-16">
            <p class="text-slate-400 text-xl">No books in the library.</p>
          </div>`;
      } else {
        books.forEach(book => {
          const status = getBookStatus(book);
          const duePart = book.dueDate
            ? `<span class="text-amber-400 font-bold text-xs">📌 ${new Date(book.dueDate).toLocaleDateString()}</span>`
            : "";
          html += `
            <div class="group backdrop-blur-xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl shadow-2xl overflow-hidden cursor-pointer transition-all duration-500 hover:scale-110 hover:shadow-2xl border border-slate-700/50 hover:border-cyan-400/50 h-72 hover:-translate-y-4"
                 data-book-id="${book.id}">
              <div class="h-32 bg-gradient-to-br from-cyan-500 via-blue-600 to-purple-600 relative overflow-hidden group-hover:via-cyan-600 transition-all duration-300">
                <div class="absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-300 bg-white"></div>
                <div class="p-5 text-white h-full flex flex-col justify-between">
                  <div>
                    <span class="text-3xl">${status.icon}</span>
                    <p class="text-xs font-semibold opacity-90 mt-1">ID: ${book.id}</p>
                  </div>
                  <span class="text-xs font-bold px-3 py-1.5 rounded-lg ${status.bg} ${status.color} w-fit border ${status.border}">
                    ${status.text}
                  </span>
                </div>
              </div>
              <div class="p-5 flex flex-col justify-between flex-1 h-40">
                <div>
                  <h3 class="font-bold text-base text-white line-clamp-2 mb-2">${book.title}</h3>
                  <p class="text-slate-400 text-xs mb-3 line-clamp-1">${book.author}</p>
                </div>
                <div class="flex justify-between items-center text-xs text-slate-400 border-t border-slate-700 pt-3">
                  <span>📅 ${book.year}</span>
                  ${duePart}
                </div>
              </div>
            </div>
          `;
        });
      }

      html += "</div>";
      container.innerHTML = html;

      document.querySelectorAll("[data-book-id]").forEach(card => {
        card.addEventListener("click", () => {
          const id = parseInt(card.getAttribute("data-book-id"));
          const book = books.find(b => b.id === id);
          if (book) openModal(book);
        });
      });
    }

    function renderSearch(container) {
      let html = `
        <h2 class="text-3xl font-bold text-white mb-6">Search Books</h2>
        <div class="mb-8">
          <input id="search-input" type="text"
                 placeholder="🔍 Search by ID, title, or author..."
                 class="w-full px-6 py-4 rounded-2xl shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 bg-slate-800/80 text-white placeholder-slate-500 border border-slate-700 transition-all duration-300 text-base" />
        </div>
        <div id="search-results" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"></div>
      `;
      container.innerHTML = html;

      const input = document.getElementById("search-input");
      const results = document.getElementById("search-results");

      function renderResults(term) {
        const t = term.toLowerCase();
        const filtered = books.filter(b =>
          b.id.toString().includes(t) ||
          b.title.toLowerCase().includes(t) ||
          b.author.toLowerCase().includes(t)
        );

        if (filtered.length === 0) {
          results.innerHTML = `
            <div class="col-span-full text-center py-16">
              <p class="text-slate-400 text-xl">No books found.</p>
            </div>`;
          return;
        }

        let htmlCards = "";
        filtered.forEach(book => {
          const status = getBookStatus(book);
          htmlCards += `
            <div class="group backdrop-blur-xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl shadow-lg overflow-hidden cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-2xl border border-slate-700/50 hover:border-cyan-400/50"
                 data-book-id="${book.id}">
              <div class="h-28 ${status.bg} p-5 flex flex-col justify-between">
                <span class="text-2xl">${status.icon}</span>
                <span class="text-xs font-bold ${status.color} w-fit">${status.text}</span>
              </div>
              <div class="p-4 bg-slate-800/80">
                <h3 class="font-bold text-white mb-2 line-clamp-2">${book.title}</h3>
                <p class="text-slate-400 text-sm line-clamp-1">${book.author}</p>
                <p class="text-slate-500 text-xs mt-2">📅 ${book.year}</p>
              </div>
            </div>
          `;
        });
        results.innerHTML = htmlCards;

        document.querySelectorAll("#search-results [data-book-id]").forEach(card => {
          card.addEventListener("click", () => {
            const id = parseInt(card.getAttribute("data-book-id"));
            const book = books.find(b => b.id === id);
            if (book) openModal(book);
          });
        });
      }

      input.addEventListener("input", () => renderResults(input.value));
      renderResults("");
    }

    function renderIssued(container) {
      const issuedBooks = books.filter(b => b.isIssued);
      let html = `
        <h2 class="text-3xl font-bold text-white mb-6">Issued Books</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      `;

      if (issuedBooks.length === 0) {
        html += `
          <div class="col-span-full text-center py-16">
            <p class="text-slate-400 text-xl">No issued books.</p>
          </div>`;
      } else {
        const today = new Date();
        issuedBooks.forEach(book => {
          const status = getBookStatus(book);
          const due = book.dueDate ? new Date(book.dueDate) : null;
          const daysLeft = due ? Math.ceil((due - today) / (1000 * 60 * 60 * 24)) : 0;
          const overdue = due && today > due;
          const badgeText = overdue
            ? `⚠️ ${Math.abs(daysLeft)} days overdue`
            : `📅 ${daysLeft} days left`;
          const badgeClass = overdue
            ? "bg-red-500/20 text-red-400"
            : "bg-blue-500/20 text-blue-400";

          html += `
            <div class="group backdrop-blur-xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl shadow-lg overflow-hidden cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-2xl border border-slate-700/50 hover:border-cyan-400/50"
                 data-book-id="${book.id}">
              <div class="h-28 ${status.bg} p-5 flex flex-col justify-between">
                <span class="text-2xl">${status.icon}</span>
                <span class="text-xs font-bold ${status.color} w-fit">${status.text}</span>
              </div>
              <div class="p-4 bg-slate-800/80">
                <h3 class="font-bold text-white mb-2 line-clamp-2">${book.title}</h3>
                <p class="text-slate-400 text-sm line-clamp-1">${book.author}</p>
                <div class="mt-3 p-2 rounded-lg text-xs font-bold ${badgeClass}">
                  ${badgeText}
                </div>
              </div>
            </div>
          `;
        });
      }

      html += "</div>";
      container.innerHTML = html;

      document.querySelectorAll("[data-book-id]").forEach(card => {
        card.addEventListener("click", () => {
          const id = parseInt(card.getAttribute("data-book-id"));
          const book = books.find(b => b.id === id);
          if (book) openModal(book);
        });
      });
    }

    function renderIssue(container) {
      const availableBooks = books.filter(b => !b.isIssued);
      let html = `
        <h2 class="text-3xl font-bold text-white mb-6">Quick Issue</h2>
        <p class="text-slate-400 mb-6 text-sm">Issue any available book directly from this list.</p>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      `;
      if (availableBooks.length === 0) {
        html += `
          <div class="col-span-full text-center py-16">
            <p class="text-slate-400 text-xl">All books are currently issued.</p>
          </div>`;
      } else {
        availableBooks.forEach(book => {
          html += `
            <div class="backdrop-blur-xl bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 border border-slate-700/50 hover:border-emerald-400/50">
              <div class="bg-gradient-to-r from-emerald-500 to-green-600 p-4">
                <h3 class="text-white font-bold text-lg line-clamp-2">${book.title}</h3>
              </div>
              <div class="p-4">
                <p class="text-slate-400 mb-2 text-sm line-clamp-2">${book.author}</p>
                <p class="text-slate-500 text-xs mb-4">📅 ${book.year}</p>
                <button class="issue-btn w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-bold py-2.5 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
                        data-book-id="${book.id}">
                  📤 Issue Book
                </button>
              </div>
            </div>
          `;
        });
      }
      html += "</div>";
      container.innerHTML = html;

      document.querySelectorAll(".issue-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const id = parseInt(btn.getAttribute("data-book-id"));
          handleIssueBook(id);
        });
      });
    }

    function renderAdd(container) {
      const html = `
        <div class="max-w-xl mx-auto backdrop-blur-xl bg-gradient-to-br from-slate-800/90 to-slate-900/90 rounded-2xl shadow-2xl p-8 border border-slate-700/60">
          <h2 class="text-3xl font-bold text-white mb-2">➕ Add New Book</h2>
          <p class="text-slate-400 mb-6 text-sm">Fill the form to expand your library collection.</p>
          <div class="space-y-4">
            <div>
              <label class="block text-white font-semibold mb-1 text-sm">Book ID</label>
              <input id="add-id" type="number" class="w-full px-4 py-2 border-2 border-slate-600 rounded-xl focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 bg-slate-700/50 text-white placeholder-slate-500" placeholder="101" />
            </div>
            <div>
              <label class="block text-white font-semibold mb-1 text-sm">Title</label>
              <input id="add-title" type="text" class="w-full px-4 py-2 border-2 border-slate-600 rounded-xl focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 bg-slate-700/50 text-white placeholder-slate-500" placeholder="Enter book title" />
            </div>
            <div>
              <label class="block text-white font-semibold mb-1 text-sm">Author</label>
              <input id="add-author" type="text" class="w-full px-4 py-2 border-2 border-slate-600 rounded-xl focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 bg-slate-700/50 text-white placeholder-slate-500" placeholder="Enter author name" />
            </div>
            <div>
              <label class="block text-white font-semibold mb-1 text-sm">Year</label>
              <input id="add-year" type="number" class="w-full px-4 py-2 border-2 border-slate-600 rounded-xl focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 bg-slate-700/50 text-white placeholder-slate-500" placeholder="2024" />
            </div>
          </div>
          <div class="flex gap-4 pt-6">
            <button id="add-submit"
                    class="flex-1 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-bold py-3 rounded-xl hover:shadow-lg transition-all duration-300 transform hover:scale-105">
              ✅ Add Book
            </button>
            <button id="add-cancel"
                    class="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-3 rounded-xl transition-all duration-300 border border-slate-600">
              Cancel
            </button>
          </div>
        </div>
      `;
      container.innerHTML = html;

      document.getElementById("add-submit").addEventListener("click", () => {
        const idVal = document.getElementById("add-id").value.trim();
        const titleVal = document.getElementById("add-title").value.trim();
        const authorVal = document.getElementById("add-author").value.trim();
        const yearVal = document.getElementById("add-year").value.trim();

        if (!idVal || !titleVal || !authorVal || !yearVal) {
          showNotification("Please fill all fields", "error");
          return;
        }

        apiAddBook({
          id: parseInt(idVal),
          title: titleVal,
          author: authorVal,
          year: parseInt(yearVal)
        }).then(res => {
          if (res.error) {
            showNotification(res.error, "error");
          } else {
            books.push(res);
            showNotification("✨ Book added successfully!", "success");
            switchView("home");
          }
          updateStatsBar();
        }).catch(() => {
          showNotification("Error adding book", "error");
        });
      });

      document.getElementById("add-cancel").addEventListener("click", () => {
        switchView("home");
      });
    }

    // --------------- MODAL HANDLING --------------------
    function openModal(book) {
      selectedBook = book;
      document.getElementById("modal-title").textContent = book.title;
      document.getElementById("modal-author").textContent = book.author;
      document.getElementById("modal-id").textContent = book.id;
      document.getElementById("modal-year").textContent = book.year;

      const status = getBookStatus(book);
      const box = document.getElementById("modal-status-box");
      const statusText = document.getElementById("modal-status-text");
      const dueEl = document.getElementById("modal-due");

      box.className = `p-4 rounded-xl border-2 ${status.bg} ${status.border}`;
      statusText.className = `font-bold text-lg ${status.color}`;
      statusText.textContent = status.text;

      if (book.dueDate) {
        dueEl.textContent = "📅 Due: " + new Date(book.dueDate).toLocaleDateString();
      } else {
        dueEl.textContent = "";
      }

      const issueBtn = document.getElementById("modal-issue-btn");
      const returnBtn = document.getElementById("modal-return-btn");

      if (book.isIssued) {
        issueBtn.classList.add("hidden");
        returnBtn.classList.remove("hidden");
      } else {
        issueBtn.classList.remove("hidden");
        returnBtn.classList.add("hidden");
      }

      document.getElementById("modal-backdrop").classList.remove("hidden");
    }

    function closeModal() {
      document.getElementById("modal-backdrop").classList.add("hidden");
      selectedBook = null;
    }

    function handleIssueBook(id) {
      apiIssueBook(id).then(res => {
        if (res.error) {
          showNotification(res.error, "error");
          return;
        }
        books = books.map(b => b.id === id ? res : b);
        showNotification("📤 Book issued!", "success");
        updateStatsBar();
        render();
        if (selectedBook && selectedBook.id === id) {
          openModal(res);
        }
      }).catch(() => {
        showNotification("Error issuing book", "error");
      });
    }

    function handleReturnBook(id) {
      apiReturnBook(id).then(res => {
        if (res.error) {
          showNotification(res.error, "error");
          return;
        }
        const updated = res.book;
        books = books.map(b => b.id === id ? updated : b);
        if (res.fine > 0) {
          showNotification(`⚠️ Overdue! Fine: Rs. ${res.fine} (${res.daysOverdue} days)`, "warning");
        } else {
          showNotification("✅ Book returned on time!", "success");
        }
        updateStatsBar();
        render();
        closeModal();
      }).catch(() => {
        showNotification("Error returning book", "error");
      });
    }

    function handleDeleteBook(id) {
      if (!confirm("Are you sure you want to delete this book?")) return;
      apiDeleteBook(id).then(() => {
        books = books.filter(b => b.id !== id);
        showNotification("🗑️ Book deleted", "info");
        updateStatsBar();
        render();
        closeModal();
      }).catch(() => {
        showNotification("Error deleting book", "error");
      });
    }

    // --------------- NAV + INIT ------------------------
    function switchView(view) {
      currentView = view;
      document.querySelectorAll(".nav-btn").forEach(btn => {
        const v = btn.getAttribute("data-view");
        if (v === view) {
          btn.className = "nav-btn px-6 py-2 rounded-xl font-bold border bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg border-cyan-400";
        } else {
          btn.className = "nav-btn px-6 py-2 rounded-xl font-bold border bg-slate-700/70 text-slate-300 border-slate-600 hover:bg-slate-600/80";
        }
      });
      render();
    }

    document.addEventListener("DOMContentLoaded", () => {
      document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          const view = btn.getAttribute("data-view");
          switchView(view);
        });
      });

      document.getElementById("modal-close-btn").addEventListener("click", closeModal);
      document.getElementById("modal-delete-btn").addEventListener("click", () => {
        if (selectedBook) handleDeleteBook(selectedBook.id);
      });
      document.getElementById("modal-issue-btn").addEventListener("click", () => {
        if (selectedBook) handleIssueBook(selectedBook.id);
      });
      document.getElementById("modal-return-btn").addEventListener("click", () => {
        if (selectedBook) handleReturnBook(selectedBook.id);
      });

      document.getElementById("modal-backdrop").addEventListener("click", (e) => {
        if (e.target.id === "modal-backdrop") closeModal();
      });

      loadBooks().then(() => {
        updateStatsBar();
        render();
      });
    });
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return Response(HTML, mimetype="text/html")

# -------------------- REPLIT → RENDER COMPATIBLE SERVER --------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))   # Render dynamically assigns PORT
    app.run(host="0.0.0.0", port=port)
