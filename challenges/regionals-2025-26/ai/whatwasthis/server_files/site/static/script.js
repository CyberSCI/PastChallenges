document.addEventListener("DOMContentLoaded", () => {
  // Get references to all necessary DOM elements
  const imageUploader = document.getElementById("image-uploader");
  const uploadLabel = document.querySelector(".upload-label");
  const statusContainer = document.getElementById("status-container");
  const statusMessage = document.getElementById("status-message");
  const resultContainer = document.getElementById("result-container");
  const resultText = document.getElementById("result-text");
  const errorMessage = document.getElementById("error-message");
  const imagePreviewContainer = document.getElementById(
    "image-preview-container",
  );
  const imagePreview = document.getElementById("image-preview");

  const VALID_FILE_TYPES = ["image/jpeg", "image/png"];

  /**
   * Resets the UI to its initial state.
   */
  const resetUI = () => {
    errorMessage.classList.add("hidden");
    resultContainer.classList.add("hidden");
    statusContainer.classList.add("hidden");
    imagePreviewContainer.classList.add("hidden");
    errorMessage.textContent = "";
    resultText.textContent = "";
    uploadLabel.classList.remove("disabled");
    imageUploader.disabled = false;
  };

  /**
   * Handles the file selection and validation.
   */
  const handleFileChange = (event) => {
    const files = event.target.files;

    // Do nothing if no file is selected
    if (files.length === 0) {
      return;
    }

    const file = files[0];
    resetUI();

    // Client-side validation for file type
    if (!VALID_FILE_TYPES.includes(file.type)) {
      errorMessage.textContent =
        "Invalid file type. Please upload a JPG or PNG file.";
      errorMessage.classList.remove("hidden");
      imageUploader.value = ""; // Clear the file input
      return;
    }

    // Display the image preview
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imagePreviewContainer.classList.remove("hidden");
    };

    reader.readAsDataURL(file);
    // If validation passes, proceed with the upload.
    handleImageUpload(file);
  };

  /**
   * Manages the UI state during the API call.
   * @param {boolean} isLoading - Whether to show the loading state.
   */
  const showLoading = (isLoading) => {
    statusContainer.classList.toggle("hidden", !isLoading);
    uploadLabel.classList.toggle("disabled", isLoading);
    imageUploader.disabled = isLoading;
  };

  /**
   * Displays the description from the API.
   * @param {string} description - The text to display.
   */
  const showResult = (description) => {
    resultText.textContent = description;
    resultContainer.classList.remove("hidden");
  };

  /**
   * Displays an error message.
   * @param {string} message - The error message to display.
   */
  const showError = (message) => {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
  };

  /**
   * Fetches the description for the given image file.
   * @param {File} file - The image file to analyze.
   */
  const getDescription = async (file) => {
    const formData = new FormData();
    formData.append("imagefile", file);

    // --- API Integration ---
    const API_URL = "/upload-image/"; // Placeholder

    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({})); // Try to parse error, but don't fail if body is not JSON
      const errorMessage =
        errorData.error || `API Error: ${response.statusText}`;
      throw new Error(errorMessage);
    }

    return response.json();
  };

  /**
   * Orchestrates the image upload process.
   * @param {File} file - The file to upload.
   */
  const handleImageUpload = async (file) => {
    resetUI();
    showLoading(true);

    try {
      const data = await getDescription(file);
      showResult(data.description);
    } catch (error) {
      const userFriendlyMessage =
        "Sorry, we could not analyze the image. Please try again.";
      console.error("API Error:", error.message);
      showError(userFriendlyMessage);
    } finally {
      showLoading(false);
      imageUploader.value = ""; // Reset file input to allow re-uploading the same file
    }
  };

  // Add the event listener to the file input
  imageUploader.addEventListener("change", handleFileChange);
});
