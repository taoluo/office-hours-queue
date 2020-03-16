import React, { useState, useEffect } from 'react'
import { Segment, Header, Icon, Button, Popup, Grid } from 'semantic-ui-react';
import RejectQuestionModal from './RejectQuestionModal';
import { gql } from 'apollo-boost';
import { useMutation } from '@apollo/react-hooks'

const START_QUESTION = gql`
  mutation StartQuestion($input: StartQuestionInput!) {
    startQuestion(input: $input) {
      question {
        id
      }
    }
  }
`;

const FINISH_QUESTION = gql`
  mutation FinishQuestion($input: FinishQuestionInput!) {
    finishQuestion(input: $input) {
      question {
        id
      }
    }
  }
`;

const UNDO_START_QUESTION = gql`
  mutation UndoStartQuestion($input: UndoStartQuestionInput!) {
    undoStartQuestion(input: $input) {
      question {
        id
      }
    }
  }
`;

const QuestionCard = (props) => {
  const [question, setQuestion] = useState(props.question);
  const [open, setOpen] = useState(false);
  const [startQuestion, startQuestionRes] = useMutation(START_QUESTION);
  const [finishQuestion, finishQuestionRes] = useMutation(FINISH_QUESTION);
  const [undoStartQuestion, undoStartQuestionRes] = useMutation(UNDO_START_QUESTION);

  const timeString = (date, isLong) => {
    if (isLong) return new Date(date).toLocaleString('en-US', {dateStyle: 'short', timeStyle: 'short'});
    else return new Date(date).toLocaleString('en-US', { hour: 'numeric', minute: 'numeric' })
  };

  const triggerModal = () => {
    setOpen(!open);
  };

  const onAnswer = async () => {
    await startQuestion({
      variables: {
        input: {
          questionId: question.id
        }
      }
    })
    props.refetch();
  };

  const onFinish = async () => {
    await finishQuestion({
      variables: {
        input: {
          questionId: question.id
        }
      }
    })
    props.refetch();
  };

  const onUndo = async () => {
    await undoStartQuestion({
      variables: {
        input: {
          questionId: question.id
        }
      }
    })
    props.refetch();
  }

  const isLoading = () => {
    return (startQuestionRes && startQuestionRes.loading) || (finishQuestionRes && 
      finishQuestionRes.loading) || (undoStartQuestionRes && undoStartQuestionRes.loading);
  };


  useEffect(() => {
    setQuestion(props.question);
  }, [props.question]);

  return (
    question && <div style={{"marginTop":"10px"}}>
      <RejectQuestionModal open={open} question={question} closeFunc={triggerModal} refetch={ props.refetch }/>
        <Segment attached="top" color="blue" clearing>
          <Grid columns="equal">
            <Grid.Row>
              <Grid.Column textAlign="left">
                <Header as="h5" style={{whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden"}}>
                  { question.askedBy.preferredName }
                </Header>
              </Grid.Column>
              <Grid.Column>
                <Header as="h5" color="blue" textAlign="right">
                  { timeString(question.timeAsked, false) }
                </Header>
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </Segment>
        <Segment attached
          tertiary={ question.timeStarted !== null }>
          { question.text }
        </Segment>
        <Segment attached="bottom" secondary textAlign="right">
          <Grid>
            <Grid.Row columns="equal">
              <Grid.Column textAlign="left">
                <Header as="h5">
                  {
                    !question.timeStarted &&
                    <Header.Content>
                      <Button compact
                        size='mini'
                        color='red'
                        content='Reject'
                        disabled={ isLoading() }
                        onClick={ triggerModal }/>
                      <Button compact
                        size='mini'
                        color='green'
                        target="_blank"
                        href={ question.videoChatUrl ? question.videoChatUrl : null }
                        icon={ question.videoChatUrl ? "video" : null }
                        content='Answer'
                        onClick={ onAnswer }
                        disabled={ isLoading() }/>
                    </Header.Content>
                  }
                  {
                    question.timeStarted &&
                    <Header.Content>
                      <Button compact
                        size='mini'
                        color='red'
                        content='Undo'
                        disabled={ isLoading() }
                        onClick={ onUndo }/>
                    </Header.Content>
                  }
                  {
                    question.timeStarted &&
                    <Header.Content>
                      <Button compact
                        size='mini'
                        color='green'
                        content='Finish'
                        disabled={ isLoading() }
                        onClick={ onFinish }/>
                    </Header.Content>
                  }
                  {
                    question.timeStarted && question.videoChatUrl &&
                    <a href={ question.videoChatUrl } target="_blank">
                      <Button compact
                        size='mini'
                        color='blue'
                        content='Join Call'/>
                    </a>
                  }
                </Header>
              </Grid.Column>
              <Grid.Column width={5} textAlign="right" only='computer mobile' style={{fontSize: "10px", whiteSpace: "nowrap", textOverflow: "ellipsis", overflow: "hidden"}}>
                {
                  question.timeStarted &&
                  <Popup wide
                    trigger= {
                      <Icon name="sync" loading/>
                    }
                    content= {
                      `Started by ${question.answeredBy.preferredName} on ${timeString(question.timeStarted, true)}`
                    }
                    basic inverted
                    position="bottom right"/>
                }
                {
                  question.tags && question.tags.length > 0 &&
                  <Popup
                  trigger= {
                    <span>{ question.tags.map(tag => " " + tag).toString() }</span>
                  }
                  content= { question.tags.map(tag => " " + tag).toString() }
                  basic inverted
                  position="bottom left"/>

                }
                {
                  (!question.tags || question.tags.length == 0) && <span><i>No Tags</i></span>
                }
               
              </Grid.Column>
            </Grid.Row>
          </Grid>
        </Segment>
      </div>
  );
}

export default QuestionCard;
