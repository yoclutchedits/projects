const gridEl = document.querySelector(".grid")
const squareEls =Array.from({length: 8}, () => Array(8).fill(null))
let selectedSquare = null;
let validMoves = [];
let currentBoard = null;
let currentPlayer = null;
let isBusy = false;
let checkSquare = null;
let pendingPromotion = null;
const moveSound = new Audio("sfx/Move.mp3");
const captureSound = new Audio("sfx/Capture.mp3");
const checkSound = new Audio("sfx/Check.mp3");
const checkmateSound = new Audio("sfx/Checkmate.mp3");
const victorySound = new Audio("sfx/Victory.mp3");
const defeatSound = new Audio("sfx/Defeat.mp3");
const errorSound = new Audio("sfx/Error.mp3");
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
function playSound(sound) {
    sound.currentTime = 0;
    sound.play().catch(() => {
        // Browser may block sound until the user interacts with the page.
    });
}

function playMoveSound(beforeBoard, afterBoard, gameState) {
    let wasCapture = false;

    // Check whether the destination square previously contained an enemy piece
    const lastMove = gameState.last_move;

    if (lastMove) {
        const [start, end] = lastMove;
        const [toRow, toCol] = end;

        const capturedPiece = beforeBoard[toRow][toCol];

        if (capturedPiece) {
            wasCapture = true;
        }

        // En passant
        const [fromRow, fromCol] = start;
        const movingPiece = beforeBoard[fromRow][fromCol];

        if (
            movingPiece &&
            movingPiece[1] === "P" &&
            fromCol !== toCol &&
            !capturedPiece
        ) {
            wasCapture = true;
        }
    }

    if (wasCapture) {
        playSound(captureSound);
    } else {
        playSound(moveSound);
    }

    if (gameState.game_over) {
        if (gameState.status_message.includes("Checkmate")) {
            // Delay slightly so checkmate sound is distinct from move sound
            setTimeout(() => playSound(checkmateSound), 100);
        }
    } else if (gameState.in_check) {
        setTimeout(() => playSound(checkSound), 100);
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
            squareEl.classList.remove("selected", "valid-move","capture" , "check");
            if (selectedSquare && selectedSquare.row === row && selectedSquare.col === col) {
                squareEl.classList.add("selected");
            }
            if (isCaptureSquare(row, col)) {
                squareEl.classList.add("capture");
            }
            else if (validMoves.some(([r, c]) => r === row && c === col)) {
                squareEl.classList.add("valid-move");
            }
            if (checkSquare && checkSquare.row === row && checkSquare.col === col) {
                squareEl.classList.add("check");
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
        const movingPiece = currentBoard[selectedSquare.row][selectedSquare.col];
        const isPromotion = movingPiece[1] === "P" && (row === 0 || row === 7);

        if (isPromotion) {
            // Don't fetch yet — save the pending move and show the picker
            isBusy = true;
            try{
            pendingPromotion = {
                fromRow: selectedSquare.row,
                fromCol: selectedSquare.col,
                toRow: row,
                toCol: col,
            };
            document.getElementById("promotion-picker").classList.remove("hidden");
            selectedSquare = null;
            validMoves = [];
            renderBoard(currentBoard);
        }
        finally {
            isBusy = false;
        }
        } else {
            isBusy = true;
            try {
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

                if (currentPlayer === "b") {
                    await triggerAiMove();
                }
                } else {
                    selectedSquare = null;
                    validMoves = [];
                    renderBoard(currentBoard);
                    showError(data.message);
                }
            } finally {
                isBusy = false;
            }
        }
    }
    else if (belongsToCurrentPlayer) {
        // Case 1: select this square, then ask the server for valid moves
        selectedSquare = { row, col };
        isBusy = true;
        try {
            const response = await fetch("http://127.0.0.1:8000/api/valid-moves", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ row: row, col: col }),
            });
            const data = await response.json();
            validMoves = data.valid_moves;
            renderBoard(currentBoard);
        } finally {
            isBusy = false;
        }
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

    playSound(errorSound);

    setTimeout(() => {
        errorBanner.classList.add("hidden");
    }, 3000);
}
function applyGameState(gameState) {
    const previousBoard = currentBoard;

    currentBoard = gameState.board;
    currentPlayer = gameState.current_player;

    selectedSquare = null;
    validMoves = [];

    if (gameState.in_check) {
        checkSquare = findKing(
            currentBoard,
            gameState.in_check_color
        );
    } else {
        checkSquare = null;
    }

    renderBoard(currentBoard);
    renderCapturedPieces(gameState.captured_pieces);
    renderMoveHistory(gameState.move_history);
    turnIndicator();

    // Play move/capture/check/checkmate sound
    if (previousBoard) {
        playMoveSound(previousBoard, currentBoard, gameState);
    }

    if (gameState.game_over) {
        showGameOver(gameState.status_message);

        if (gameState.status_message.includes("Checkmate")) {
            // Determine winner
            // After a move, current_player is the player who would move next.
            // Therefore the opposite color won.
            const winner = currentPlayer === "w" ? "Black" : "White";

            if (winner === "White") {
                playSound(victorySound);
            } else {
                playSound(defeatSound);
            }
        }
    }
}
function renderCapturedPieces(capturedPieces) {
    const capturedWhiteEl = document.getElementById("captured-white");
    const capturedBlackEl = document.getElementById("captured-black");
    capturedWhiteEl.innerHTML = "";
    capturedBlackEl.innerHTML = "";

    for (const piece of capturedPieces) {
        const pieceEl = document.createElement("img");
        pieceEl.src = `pieces/${piece}.png`;
        pieceEl.classList.add("captured-piece");

        if (piece[0] === "w") {
            capturedWhiteEl.appendChild(pieceEl);
        } else {
            capturedBlackEl.appendChild(pieceEl);
        }
    }
}
function renderMoveHistory(moveHistory) {
    const moveHistoryEl = document.getElementById("move-history");
    moveHistoryEl.innerHTML = "";
    for (const move of moveHistory) {
        const moveEl = document.createElement("div");
        moveEl.textContent = move;
        moveHistoryEl.appendChild(moveEl);
    }
}
function turnIndicator() {
    const turnIndicatorEl = document.getElementById("turn-indicator");
    if (currentPlayer === "w") {
        turnIndicatorEl.textContent = "White's Turn";
    } else {
        turnIndicatorEl.textContent = "Black's Turn";
    }
}
function showGameOver(message) {
    const gameOverBanner = document.getElementById("game-over-banner");
    const gameOverMessage = document.getElementById("game-over-message");
    gameOverMessage.textContent = message;
    gameOverBanner.classList.remove("hidden");
}
async function resetGame() {
    const request =await fetch("http://127.0.0.1:8000/api/reset", {
        method: "POST"
    })
    const data = await request.json()
        if (data.success) {
            applyGameState(data.game_state);
            const gameOverBanner = document.getElementById("game-over-banner");
            gameOverBanner.classList.add("hidden");
        } else {
            showError("Failed to reset the game.");
        }
}
function showResetConfirm() {
    const resetConfirmBanner = document.getElementById("reset-confirm-banner");
    resetConfirmBanner.classList.remove("hidden");
}
function hideResetConfirm() {
    const resetConfirmBanner = document.getElementById("reset-confirm-banner");
    resetConfirmBanner.classList.add("hidden");
}
function findKing(board, color) {
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const piece = board[row][col];
            if (piece && piece[0] === color && piece[1] === "K") {
                return { row, col };
            }
        }
    }
    return null; // shouldn't happen in a normal game, but good practice
}
async function choosePromotion(piece) {
    if (!pendingPromotion) return;

    isBusy = true;

    document.getElementById("promotion-picker").classList.add("hidden");

    try {
        const response = await fetch("http://127.0.0.1:8000/api/move", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                from_row: pendingPromotion.fromRow,
                from_col: pendingPromotion.fromCol,
                to_row: pendingPromotion.toRow,
                to_col: pendingPromotion.toCol,
                promote_to: piece,
            }),
        });

        const data = await response.json();

        if (data.success) {
            applyGameState(data.game_state);

            // currentPlayer is now the next player.
            if (currentPlayer === "b") {
                await triggerAiMove();
            }
        } else {
            showError(data.message);
        }
    } catch (error) {
        console.error(error);
        showError("Failed to make promotion move.");
    } finally {
        pendingPromotion = null;
        isBusy = false;
    }
}
async function loadBoard() {
    let response= await fetch("http://127.0.0.1:8000/api/board")
    const data = await response.json()
    currentBoard = data.board;
    currentPlayer = data.current_player;
    if (data.in_check) {
        checkSquare = findKing(currentBoard, data.in_check_color);
    } else {
        checkSquare = null;
    }
    renderBoard(data.board);
    renderCapturedPieces(data.captured_pieces);
    renderMoveHistory(data.move_history);
    turnIndicator();
    }

loadBoard();