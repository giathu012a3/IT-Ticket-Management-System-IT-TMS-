CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(120) NOT NULL,
    full_name VARCHAR(120),
    role VARCHAR(20) DEFAULT 'user'
);

CREATE TABLE ticket (
    id INTEGER PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'New',
    priority VARCHAR(20) DEFAULT 'Medium',
    category VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    creator_id INTEGER NOT NULL,
    assigned_to_id INTEGER,
    FOREIGN KEY (creator_id) REFERENCES user(id),
    FOREIGN KEY (assigned_to_id) REFERENCES user(id)
);

CREATE TABLE comment (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_internal BOOLEAN DEFAULT 0,
    user_id INTEGER NOT NULL,
    ticket_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (ticket_id) REFERENCES ticket(id)
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES ticket(id)
);

CREATE TABLE notification (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message VARCHAR(255) NOT NULL,
    link VARCHAR(255),
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
