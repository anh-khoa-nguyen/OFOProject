<script>
  const carousel = document.getElementById('carousel');
  const arrowLeft = document.getElementById('arrowLeft');
  const arrowRight = document.getElementById('arrowRight');

  const scrollByAmount = carousel.offsetWidth / 4; // 1 card

  function updateArrows() {
    arrowLeft.classList.toggle('d-none', carousel.scrollLeft === 0);
    arrowRight.classList.toggle(
      'd-none',
      carousel.scrollLeft + carousel.offsetWidth >= carousel.scrollWidth
    );
  }

  arrowLeft.addEventListener('click', () => {
    carousel.scrollBy({ left: -scrollByAmount, behavior: 'smooth' });
    setTimeout(updateArrows, 300);
  });

  arrowRight.addEventListener('click', () => {
    carousel.scrollBy({ left: scrollByAmount, behavior: 'smooth' });
    setTimeout(updateArrows, 300);
  });

  window.addEventListener('load', updateArrows);
  window.addEventListener('resize', updateArrows);
</script>