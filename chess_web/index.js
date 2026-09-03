const gridEl = document.querySelector(".grid")
const squareEls =Array.from({length: 8}, () => Array(8).fill(null))
let selectedSquare = null;
let validMoves = [];
let currentBoard = null;
let currentPlayer = null;
let isBusy = false;
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

function isCaptureSquare(row, col) {
    if (!selectedSquare || !validMoves.some(([r, c]) => r === row && c === col)) return false;
    const sourcePiece = currentBoard[selectedSquare.row][selectedSquare.col];
    const targetPiece = currentBoard[row][col];
    if (!sourcePiece) return false;

    // Standard capture
    if (targetPiece && targetPiece[0] !== sourcePiece[0]) return true;

    // En Passant capture (Pawn moving diagonally onto an empty square)
    if (sourcePiece[1] === "P" && selectedSquare.col !== col && !targetPiece) return true;

    return false;
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
            squareEl.classList.remove("selected", "valid-move","capture");
            if (selectedSquare && selectedSquare.row === row && selectedSquare.col === col) {
                squareEl.classList.add("selected");
            }
            if (isCaptureSquare(row, col)) {
                squareEl.classList.add("capture");
            }
            else if (validMoves.some(([r, c]) => r === row && c === col)) {
                squareEl.classList.add("valid-move");
            }
        }
    }
}
async function onSquareClick(row, col) {
    const piece = currentBoard[row][col];
    const belongsToCurrentPlayer = piece && piece[0] === currentPlayer;
    
    const isValidTarget = validMoves.some(([r, c]) => r === row && c === col);
    if (isBusy) {
        showError("Please wait for the current move to finish.");
        return;
    }
    if (selectedSquare && isValidTarget) {
        // NEW: Case 0 — make the move
        isBusy = true;
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
                applyGameState(data.game_state);

            } else {
                selectedSquare = null;
                validMoves = [];
                renderBoard(currentBoard);
                showError(data.message)

            }
        if (currentPlayer === "b") {
            await triggerAiMove();
        }
        isBusy = false;
    }
    else if ( belongsToCurrentPlayer) {
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
    if (response.status === 429) {
        showError("AI is rate-limited — try again shortly.");
        return;
    }
    const data = await response.json();
    
    if (data.success) {
        applyGameState(data.game_state);
    }
    else {
        showError(data.message || "AI move failed.");
    }
}
function showError(message) {
    const errorBanner = document.getElementById("error-banner");
    errorBanner.textContent = message;
    errorBanner.classList.remove("hidden");
    setTimeout(() => {
        errorBanner.classList.add("hidden");
    }, 3000);
}
function applyGameState(gameState) {
    currentBoard = gameState.board;
    currentPlayer = gameState.current_player;
    selectedSquare = null;
    validMoves = [];
    renderBoard(currentBoard);

    if (gameState.game_over) {
        showGameOver(gameState.status_message);
    }
}
function showGameOver(message) {
    const gameOverBanner = document.getElementById("game-over-banner");
    gameOverBanner.textContent = message;
    gameOverBanner.classList.remove("hidden");
}
async function loadBoard() {
let response= await fetch("http://127.0.0.1:8000/api/board")
const data = await response.json()
currentBoard = data.board;
currentPlayer = data.current_player;
renderBoard(data.board);
 }

loadBoard();