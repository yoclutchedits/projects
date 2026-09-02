const gridEl = document.querySelector(".grid")
const squareEls =Array.from({length: 8}, () => Array(8).fill(null))
let selectedSquare = null;
let validMoves = [];
let currentBoard = null;
let currentPlayer = null;
for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
        const square = document.createElement("div")
        square.addEventListener("click", () => onSquareClick(row, col))
        if ((row+col) % 2 == 0){
            square.classList.add("white");
        }
        else{
            square.classList.add("black");
        }
        squareEls[row][col] = square;
        gridEl.appendChild(square)
    }
}
function renderBoard(board) {
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const piece = board[row][col];
            const squareEl = squareEls[row][col];
            if (piece) {
                squareEl.style.backgroundImage = "url('pieces/" + piece + ".png')";
            } else {
                squareEl.style.backgroundImage = "";
            }
            squareEl.classList.remove("selected", "valid-move");
            if (selectedSquare && selectedSquare.row === row && selectedSquare.col === col) {
                squareEl.classList.add("selected");
            }
            if (validMoves.some(([r, c]) => r === row && c === col)) {
                squareEl.classList.add("valid-move");
            }
        }
    }
}
async function onSquareClick(row, col) {
    const piece = currentBoard[row][col];
    const belongsToCurrentPlayer = piece && piece[0] === currentPlayer;
    
    const isValidTarget = validMoves.some(([r, c]) => r === row && c === col);
    if (selectedSquare && isValidTarget) {
        // NEW: Case 0 — make the move
        const response = await fetch("http://127.0.0.1:8000/api/move", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                from_row: selectedSquare.row,
                from_col: selectedSquare.col,
                to_row: row,
                to_col: col,
            }),
        });
        const data = await response.json();
        if (data.success) {
                currentBoard = data.game_state.board;
                currentPlayer = data.game_state.current_player;
                selectedSquare = null;
                validMoves = [];
                renderBoard(currentBoard);
            } else {
                selectedSquare = null;
                validMoves = [];
                renderBoard(currentBoard);
            }
        if (currentPlayer === "b") {
            await triggerAiMove();
        }
    }
    else if (!selectedSquare && belongsToCurrentPlayer) {
        // Case 1: select this square, then ask the server for valid moves
        selectedSquare = { row, col };
        const response = await fetch("http://127.0.0.1:8000/api/valid-moves", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ row: row, col: col }),
        });
        const data = await response.json();
        validMoves = data.valid_moves;
        renderBoard(currentBoard);
    } else {
        // Case 2: clear selection
        selectedSquare = null;
        validMoves = [];
        renderBoard(currentBoard);
    }
}

async function triggerAiMove() {
    const response = await fetch("http://127.0.0.1:8000/api/ai-move", {
        method: "POST",
    });
    const data = await response.json();
    if (data.success) {
        currentBoard = data.game_state.board;
        currentPlayer = data.game_state.current_player;
        selectedSquare = null;
        validMoves = [];
        renderBoard(currentBoard);
    }
}

async function loadBoard() {
let response= await fetch("http://127.0.0.1:8000/api/board")
const data = await response.json()
currentBoard = data.board;
currentPlayer = data.current_player;
renderBoard(data.board);
 }

loadBoard();