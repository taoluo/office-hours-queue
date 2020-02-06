import React from 'react';
import { Segment, Menu, Grid, Image } from 'semantic-ui-react';
import { withFirebase } from '../Firebase';
import { Link } from 'react-router-dom';

const CourseSidebar = (props) => (
  <Grid.Column width={3}>
    <Segment basic>
    <Link to='/home'>
      <Image src='../../../ohq.png' size='tiny' style={{"marginTop":"10px"}}/>
    </Link>
    <Menu vertical secondary fluid>
      <Menu.Item
        name="Queue"
        icon='hourglass one'
        active={props.active === 'queue'}
        color='blue'
        onClick={ () => props.clickFunc('queue') }/>
      <Menu.Item
        name="Roster"
        icon='users'
        active={props.active === 'roster'}
        color='blue'
        onClick={ () => props.clickFunc('roster') }/>
      <Menu.Item
        name="Analytics"
        icon='chart bar'
        active={props.active === 'analytics'}
        color='blue'
        onClick={ () => props.clickFunc('analytics') }/>
      <Menu.Item
        name="Course Settings"
        icon='settings'
        active={props.active === 'course_settings'}
        color='blue'
        onClick={ () => props.clickFunc('course_settings') }/>
    </Menu>
    </Segment>
  </Grid.Column>
);

export default withFirebase(CourseSidebar);
