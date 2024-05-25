import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import './BookDetails.css';

const BookDetails = () => {
  const { id } = useParams();
  const [book, setBook] = useState(null);
  const [review, setReview] = useState('');
  const [reviews, setReviews] = useState([]);
  const [isReviewFormVisible, setReviewFormVisible] = useState(false);

  useEffect(() => {
    const fetchBook = async () => {
      try {
        const response = await axios.get(`http://localhost:5000/books/${id}`);
        setBook(response.data);
        setReviews(response.data.reviews || []);
      } catch (error) {
        console.error('Error fetching book:', error);
      }
    };
    fetchBook();
  }, [id]);

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await axios.post(
          'http://localhost:5000/reviews',
          { book_id: book.id, review },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const newReview = { body: review, user: { name: response.data.user.name } };
        setReviews([...reviews, newReview]);
        setReview('');
        setReviewFormVisible(false);
      } catch (error) {
        console.error('Error adding review:', error);
      }
    } else {
      alert('You need to be logged in to add a review.');
    }
  };

  return (
    <div className="book-details-container">
      {book ? (
        <>
          <div className="book-card">
            <img className="book-image" src={book.image_url} alt={book.title} />
            <h2>{book.title}</h2>
            <p>{book.author}</p>
            <button className="add-to-list-button">Add to My List</button>
          </div>
          <div className="reviews-section">
            <h3>Reviews</h3>
            <button className="add-review-button" onClick={() => setReviewFormVisible(true)}>Add a Review</button>
            {isReviewFormVisible && (
              <form className="review-form" onSubmit={handleReviewSubmit}>
                <textarea
                  value={review}
                  onChange={(e) => setReview(e.target.value)}
                  placeholder="Write your review here"
                />
                <button type="submit">Submit Review</button>
              </form>
            )}
            <ul className="reviews-list">
              {reviews.map((r, index) => (
                <li key={index} className="review-item">
                  <p><strong>{r.user.name}:</strong> {r.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default BookDetails;
