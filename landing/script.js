const form = document.querySelector('#waitlistForm');
const statusBox = document.querySelector('#formStatus');

function setError(id, message) {
  const field = document.querySelector(`#${id}`);
  const error = document.querySelector(`#${id}Error`);

  field.setAttribute('aria-invalid', message ? 'true' : 'false');
  error.textContent = message;
}

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const name = form.parentName.value.trim();
  const email = form.email.value.trim();
  const consent = form.consent.checked;
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  setError(
    'parentName',
    name.length < 2 ? 'Wpisz swoje imię.' : ''
  );

  setError(
    'email',
    !emailPattern.test(email) ? 'Wpisz poprawny adres e-mail.' : ''
  );

  setError(
    'consent',
    !consent ? 'Zaznacz zgodę, aby dołączyć do listy.' : ''
  );

  statusBox.className = 'form-status';

  if (name.length < 2 || !emailPattern.test(email) || !consent) {
    return;
  }

  const signup = {
    parentName: name,
    email,
    subject: form.subject.value,
    grade: form.grade.value,
    createdAt: new Date().toISOString()
  };

  try {
    const signups = JSON.parse(
      localStorage.getItem('umiemto_waitlist_demo') || '[]'
    );

    const emailAlreadyExists = signups.some(
      (item) => item.email.toLowerCase() === email.toLowerCase()
    );

    if (!emailAlreadyExists) {
      signups.push(signup);
    }

    localStorage.setItem(
      'umiemto_waitlist_demo',
      JSON.stringify(signups)
    );
  } catch (error) {
    console.warn('Nie udało się zapisać formularza lokalnie.', error);
  }

  statusBox.textContent =
    'Formularz działa w wersji demonstracyjnej. Po podłączeniu systemu zapisów zgłoszenie będzie wysyłane do UmiemTo.';

  statusBox.className = 'form-status show notice';

  form.reset();
});

document.querySelector('#year').textContent =
  new Date().getFullYear();
