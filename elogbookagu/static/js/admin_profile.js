document.addEventListener('DOMContentLoaded', () => {
  // --- Modal Controls ---
  const openModalButton = document.getElementById('openModal')
  const closeModalButton = document.getElementById('closeModal')
  const editModal = document.getElementById('editModal')

  if (openModalButton && editModal) {
    openModalButton.addEventListener('click', () => {
      editModal.classList.remove('hidden')
      editModal.setAttribute('aria-hidden', 'false') // Accessibility
      // Optionally focus the first input field
      const firstInput = editModal.querySelector('input, button')
      if (firstInput) {
        firstInput.focus()
      }
    })
  }

  if (closeModalButton && editModal) {
    closeModalButton.addEventListener('click', closeModal)
  }

  if (editModal) {
    // Close modal if clicking outside the content area
    editModal.addEventListener('click', (event) => {
      if (event.target === editModal) {
        closeModal()
      }
    })
    // Close modal on Escape key press
    editModal.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeModal()
      }
    })
  }

  function closeModal() {
    if (editModal) {
      editModal.classList.add('hidden')
      editModal.setAttribute('aria-hidden', 'true') // Accessibility
    }
    // Return focus to the button that opened the modal
    if (openModalButton) {
      openModalButton.focus()
    }
  }

  // --- Profile Photo Upload ---
  const photoUploadInput = document.getElementById('profile-photo-upload')
  const photoForm = document.getElementById('profile-photo-form')

  if (photoUploadInput && photoForm) {
    photoUploadInput.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        // Consider adding a visual indicator that upload is happening
        htmx.trigger(photoForm, 'submit')
      }
    })
  }

  // --- HTMX Response Handling ---
  document.body.addEventListener('htmx:afterRequest', (event) => {
    // Check if the request originated from within our profile page context if needed
    // e.g., by checking event.detail.elt (the element triggering the request)

    if (!event.detail.successful) {
      console.error('HTMX request failed:', event.detail.xhr)
      alert('An error occurred. Please try again.')
      // Potentially parse event.detail.xhr.responseText for a server error message
      return
    }

    try {
      const response = JSON.parse(event.detail.xhr.responseText)

      if (response.success) {
        // Profile Photo Update
        if (response.profile_photo) {
          const profileImage = document.querySelector('img[alt="Profile Photo"]')
          if (profileImage) {
            profileImage.src = response.profile_photo // Update image source
            // Add a timestamp query parameter to force browser refresh if needed:
            // profileImage.src = response.profile_photo + '?t=' + new Date().getTime();
          }
          // Consider a more subtle success notification than alert()
          showToast('Profile photo updated successfully!')
        }
        // Contact Info Update
        else if (response.phone !== undefined || response.city !== undefined || response.country !== undefined) {
          const phoneText = document.getElementById('phone-text')
          const cityText = document.getElementById('city-text')
          const countryText = document.getElementById('country-text')

          if (phoneText) phoneText.textContent = response.phone ?? '' // Use nullish coalescing
          if (cityText) cityText.textContent = response.city ?? ''
          if (countryText) countryText.textContent = response.country ?? ''

          closeModal() // Close modal on successful update
          showToast('Contact information updated successfully!')
        }
      } else {
        // Handle specific errors from the server
        alert(response.error || 'Failed to update information.')
        console.error('Server returned error:', response.error)
      }
    } catch (error) {
      console.error('Error parsing JSON response or processing update:', error, event.detail.xhr.responseText)
      alert('An error occurred while processing the update.')
    }
  })

  // Simple Toast Notification Function (Example)
  function showToast(message) {
    // You can implement a more sophisticated toast notification system
    console.log('Toast:', message) // Placeholder
    // Example: Create a temporary div, style it, append to body, remove after delay
    const toast = document.createElement('div')
    toast.textContent = message
    toast.style.position = 'fixed'
    toast.style.bottom = '20px'
    toast.style.left = '50%'
    toast.style.transform = 'translateX(-50%)'
    toast.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'
    toast.style.color = 'white'
    toast.style.padding = '10px 20px'
    toast.style.borderRadius = '5px'
    toast.style.zIndex = '1000'
    document.body.appendChild(toast)
    setTimeout(() => {
      toast.remove()
    }, 3000) // Remove after 3 seconds
  }
})