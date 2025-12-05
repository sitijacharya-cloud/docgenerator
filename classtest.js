// ------------------------------
// 1. BASE CLASS (Parent)
// ------------------------------
class Item {
    constructor(id, title) {
        this.id = id;
        this.title = title;
    }

    getInfo() {
        return `${this.title} (ID: ${this.id})`;
    }
}


// ------------------------------
// 2. INHERITANCE (Book, Magazine inherit Item)
// ------------------------------
class Book extends Item {
    constructor(id, title, author, pages) {
        super(id, title);
        this.author = author;
        this.pages = pages;
    }

    getInfo() {
        return `Book: ${this.title} by ${this.author}`;
    }
}

class Magazine extends Item {
    constructor(id, title, issue) {
        super(id, title);
        this.issue = issue;
    }

    getInfo() {
        return `Magazine: ${this.title}, Issue ${this.issue}`;
    }
}


// ------------------------------
// 3. MULTI-LEVEL INHERITANCE
// ------------------------------
class DigitalBook extends Book {
    constructor(id, title, author, pages, fileSizeMb) {
        super(id, title, author, pages);
        this.fileSizeMb = fileSizeMb;
    }

    getInfo() {
        return `eBook: ${this.title} (Size: ${this.fileSizeMb}MB)`;
    }
}


// ------------------------------
// 4. COMPOSITION (A Library HAS books)
// ------------------------------
class Library {
    constructor(name) {
        this.name = name;
        this.items = []; // Library COMPOSES items
    }

    addItem(item) {
        this.items.push(item);
    }

    listItems() {
        return this.items.map(item => item.getInfo());
    }
}


// ------------------------------
// 5. AGGREGATION (Library Member has a reference to Library)
// ------------------------------
class Member {
    constructor(name, library) {
        this.name = name;
        this.library = library; // AGGREGATION: Member depends on Library
        this.borrowed = [];
    }

    borrow(itemId) {
        const item = this.library.items.find(i => i.id === itemId);
        if (item) {
            this.borrowed.push(item);
            console.log(`${this.name} borrowed: ${item.title}`);
        }
    }
}


// ------------------------------
// 6. POLYMORPHISM (different getInfo() methods)
// ------------------------------
function printItemDetails(item) {
    // Same function works for Book, Magazine, DigitalBook
    console.log(item.getInfo());
}


// ------------------------------
// 7. SIMULATED INTERFACE (optional)
// ------------------------------
class Printable {
    print() {
        throw new Error("print() must be implemented");
    }
}

class PrintableBook extends Book {
    print() {
        console.log(`Printing ${this.title}...`);
    }
}


// ------------------------------
// 8. USAGE
// ------------------------------
const library = new Library("City Library");

// Items
const book1 = new Book(1, "Clean Code", "Robert C. Martin", 450);
const mag1 = new Magazine(2, "National Geographic", 202);
const ebook1 = new DigitalBook(3, "AI Revolution", "John Doe", 300, 5);

library.addItem(book1);
library.addItem(mag1);
library.addItem(ebook1);

// Member (Aggregation)
const member = new Member("Sitij", library);
member.borrow(1); // borrow Clean Code

// Polymorphism Example
printItemDetails(book1);
printItemDetails(mag1);
printItemDetails(ebook1);

console.log("\nLibrary Collection:");
console.log(library.listItems());
