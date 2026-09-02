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

    if (!selectedSquare && belongsToCurrentPlayer) {
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

async function loadBoard() {
let response= await fetch("http://127.0.0.1:8000/api/board")
const data = await response.json()
currentBoard = data.board;
currentPlayer = data.current_player;
renderBoard(data.board);
 }

loadBoard();