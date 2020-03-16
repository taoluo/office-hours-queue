import React, {useState} from 'react';
import { Form, Modal, Button, Segment } from 'semantic-ui-react';
import { gql } from 'apollo-boost';
import { useMutation } from '@apollo/react-hooks';

/* GRAPHQL QUERIES/MUTATIONS */
const REJECT_QUESTION = gql`
  mutation RejectQuestion($input: RejectQuestionInput!) {
    rejectQuestion(input: $input) {
      question {
        id
      }
    }
  }
`;

const rejectOptions = [
  {key: 'NOT_HERE', value: 'NOT_HERE', text: 'Not Here'},
  {key: 'OH_ENDED', value: 'OH_ENDED', text: 'OH Ended'},
  {key: 'NOT_SPECIFIC', value: 'NOT_SPECIFIC', text: 'Not Specific'},
  {key: 'WRONG_QUEUE', value: 'WRONG_QUEUE', text: 'Wrong Queue'},
  {key: 'OTHER', value: 'OTHER', text: 'Other'}
];

const RejectQuestionModal = (props) => {
  const [question, setQuestion] = useState(props.question);
  const [input, setInput] = useState({questionId:props.question.id, rejectedReason: null});
  const [otherDisabled, setOtherDisabled] = useState(true);
  const [rejectDisabled, setRejectDisabled] = useState(true);
  const [rejectQuestion, { loading, error }] = useMutation(REJECT_QUESTION);

  const handleInputChange = (e, {name, value}) =>{
    input[name] = value;
    setInput(input);
    setOtherDisabled(name === 'rejectedReason' && value !== 'OTHER');

    if (name === 'rejectedReason' && value !== 'OTHER') {
      setRejectDisabled(false)
    } else if (name === 'rejectedReason' && value === 'OTHER') {
      setRejectDisabled(true)
    }
    if (name === 'rejectedReasonOther') {
      setRejectDisabled(input.rejectedReasonOther === null || input.rejectedReasonOther === '')
    }
  };

  const onSubmit = async () => {
    if (input.rejectedReason) {
      await rejectQuestion({
        variables: {
          input: input
        }
      });
      await props.refetch();
      props.closeFunc();
    }
  };

  return (
    question && <Modal open={ props.open }>
        <Modal.Header>Reject Question</Modal.Header>
        <Modal.Content>
          <Modal.Description>
            You are about to reject the following question from
            <b>{" " + question.askedBy.preferredName}</b>:<br/>
            <Segment inverted color="blue">{`"${question.text}"`}</Segment>
            <Form>
              <Form.Field required>
                <Form.Dropdown
                   name="rejectedReason"
                   placeholder="Select Reason"
                   options={rejectOptions}
                   selection
                   onChange={handleInputChange}/>
              </Form.Field>
              { input.rejectedReason === "OTHER" &&
                <Form.Field required>
                  <Form.TextArea
                    disabled={otherDisabled}
                    name="rejectedReasonOther"
                    onChange={handleInputChange}
                    placeholder={'Please add additional explanation'}/>
                </Form.Field>
              }
            </Form>
          </Modal.Description>
        </Modal.Content>
        <Modal.Actions>
          <Button content="Cancel" onClick={props.closeFunc}/>
          <Button content="Reject" disabled={rejectDisabled} color="red" onClick={onSubmit}/>
        </Modal.Actions>
      </Modal>
  );
};

export default RejectQuestionModal;